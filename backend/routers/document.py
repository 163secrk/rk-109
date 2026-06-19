from typing import List, Optional
from datetime import datetime
import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from database import get_db
import models
import schemas
from auth import get_current_user
from permissions import PermissionChecker

router = APIRouter(prefix="/api/document", tags=["文档协作"])
require_document = PermissionChecker("document")


def _get_current_team_id(user: models.User, db: Session) -> int:
    member = (
        db.query(models.TeamMember)
        .filter(models.TeamMember.user_id == user.id, models.TeamMember.is_active == True)
        .first()
    )
    if member:
        return member.team_id
    return None


def _build_doc_tree(docs):
    doc_map = {}
    root_docs = []

    for doc in docs:
        doc_dict = schemas.KnowledgeDocTreeNode.model_validate(doc).model_dump()
        doc_dict["children"] = []
        doc_map[doc.id] = doc_dict

    for doc_id, doc_dict in doc_map.items():
        parent_id = doc_dict.get("parent_id")
        if parent_id and parent_id in doc_map:
            doc_map[parent_id]["children"].append(doc_dict)
        else:
            root_docs.append(doc_dict)

    def sort_docs(docs_list):
        docs_list.sort(key=lambda x: (x.get("sort_order", 0), x.get("id", 0)))
        for doc in docs_list:
            if doc["children"]:
                sort_docs(doc["children"])

    sort_docs(root_docs)
    return root_docs


@router.get("/knowledge/tree", response_model=List[schemas.KnowledgeDocTreeNode], dependencies=[Depends(require_document)])
def list_knowledge_tree(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team_id = _get_current_team_id(current_user, db)
    if not team_id:
        raise HTTPException(status_code=403, detail="您还没有加入任何团队")

    docs = (
        db.query(models.KnowledgeDoc)
        .filter(models.KnowledgeDoc.team_id == team_id)
        .order_by(models.KnowledgeDoc.sort_order, models.KnowledgeDoc.id)
        .all()
    )

    return _build_doc_tree(docs)


@router.get("/knowledge/docs/{doc_id}", response_model=schemas.KnowledgeDocInfo, dependencies=[Depends(require_document)])
def get_knowledge_doc(
    doc_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = (
        db.query(models.KnowledgeDoc)
        .options(
            joinedload(models.KnowledgeDoc.creator),
            joinedload(models.KnowledgeDoc.updater),
        )
        .filter(models.KnowledgeDoc.id == doc_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    team_id = _get_current_team_id(current_user, db)
    if doc.team_id != team_id:
        raise HTTPException(status_code=403, detail="无权访问该文档")

    return schemas.KnowledgeDocInfo.model_validate(doc)


@router.post("/knowledge/docs", response_model=schemas.KnowledgeDocInfo, dependencies=[Depends(require_document)])
def create_knowledge_doc(
    data: schemas.KnowledgeDocCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team_id = _get_current_team_id(current_user, db)
    if not team_id:
        raise HTTPException(status_code=403, detail="您还没有加入任何团队")

    if data.parent_id:
        parent_doc = db.query(models.KnowledgeDoc).filter(models.KnowledgeDoc.id == data.parent_id).first()
        if not parent_doc:
            raise HTTPException(status_code=404, detail="父目录不存在")
        if parent_doc.team_id != team_id:
            raise HTTPException(status_code=403, detail="无权访问该目录")

    max_sort = (
        db.query(models.KnowledgeDoc)
        .filter(
            models.KnowledgeDoc.team_id == team_id,
            models.KnowledgeDoc.parent_id == data.parent_id,
        )
        .count()
    )

    doc = models.KnowledgeDoc(
        team_id=team_id,
        parent_id=data.parent_id,
        title=data.title,
        content=data.content,
        doc_type=data.doc_type,
        sort_order=max_sort,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    doc = (
        db.query(models.KnowledgeDoc)
        .options(
            joinedload(models.KnowledgeDoc.creator),
            joinedload(models.KnowledgeDoc.updater),
        )
        .filter(models.KnowledgeDoc.id == doc.id)
        .first()
    )
    return schemas.KnowledgeDocInfo.model_validate(doc)


@router.put("/knowledge/docs/{doc_id}", response_model=schemas.KnowledgeDocInfo, dependencies=[Depends(require_document)])
def update_knowledge_doc(
    doc_id: int,
    data: schemas.KnowledgeDocUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.query(models.KnowledgeDoc).filter(models.KnowledgeDoc.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    team_id = _get_current_team_id(current_user, db)
    if doc.team_id != team_id:
        raise HTTPException(status_code=403, detail="无权访问该文档")

    if data.title is not None:
        doc.title = data.title
    if data.content is not None:
        doc.content = data.content
    if data.parent_id is not None:
        if data.parent_id == doc_id:
            raise HTTPException(status_code=400, detail="父目录不能是自己")
        if data.parent_id:
            parent_doc = db.query(models.KnowledgeDoc).filter(models.KnowledgeDoc.id == data.parent_id).first()
            if not parent_doc:
                raise HTTPException(status_code=404, detail="父目录不存在")
        doc.parent_id = data.parent_id
    if data.sort_order is not None:
        doc.sort_order = data.sort_order

    doc.updated_by = current_user.id
    db.commit()
    db.refresh(doc)

    doc = (
        db.query(models.KnowledgeDoc)
        .options(
            joinedload(models.KnowledgeDoc.creator),
            joinedload(models.KnowledgeDoc.updater),
        )
        .filter(models.KnowledgeDoc.id == doc.id)
        .first()
    )
    return schemas.KnowledgeDocInfo.model_validate(doc)


@router.post("/knowledge/docs/{doc_id}/move", response_model=schemas.KnowledgeDocInfo, dependencies=[Depends(require_document)])
def move_knowledge_doc(
    doc_id: int,
    data: schemas.KnowledgeDocMove,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.query(models.KnowledgeDoc).filter(models.KnowledgeDoc.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    team_id = _get_current_team_id(current_user, db)
    if doc.team_id != team_id:
        raise HTTPException(status_code=403, detail="无权访问该文档")

    if data.parent_id == doc_id:
        raise HTTPException(status_code=400, detail="父目录不能是自己")

    if data.parent_id:
        parent_doc = db.query(models.KnowledgeDoc).filter(models.KnowledgeDoc.id == data.parent_id).first()
        if not parent_doc:
            raise HTTPException(status_code=404, detail="父目录不存在")
        if parent_doc.team_id != team_id:
            raise HTTPException(status_code=403, detail="无权访问该目录")

        def is_descendant(ancestor_id, descendant_id):
            current = descendant_id
            while current:
                if current == ancestor_id:
                    return True
                d = db.query(models.KnowledgeDoc).filter(models.KnowledgeDoc.id == current).first()
                current = d.parent_id if d else None
            return False

        if is_descendant(doc_id, data.parent_id):
            raise HTTPException(status_code=400, detail="不能将文档移动到其子目录下")

    doc.parent_id = data.parent_id
    doc.sort_order = data.sort_order
    doc.updated_by = current_user.id
    db.commit()
    db.refresh(doc)

    siblings = (
        db.query(models.KnowledgeDoc)
        .filter(
            models.KnowledgeDoc.team_id == team_id,
            models.KnowledgeDoc.parent_id == data.parent_id,
            models.KnowledgeDoc.id != doc_id,
        )
        .order_by(models.KnowledgeDoc.sort_order, models.KnowledgeDoc.id)
        .all()
    )
    for idx, sib in enumerate(siblings):
        if idx >= data.sort_order:
            sib.sort_order = idx + 1
        else:
            sib.sort_order = idx
    db.commit()

    doc = (
        db.query(models.KnowledgeDoc)
        .options(
            joinedload(models.KnowledgeDoc.creator),
            joinedload(models.KnowledgeDoc.updater),
        )
        .filter(models.KnowledgeDoc.id == doc.id)
        .first()
    )
    return schemas.KnowledgeDocInfo.model_validate(doc)


@router.delete("/knowledge/docs/{doc_id}", dependencies=[Depends(require_document)])
def delete_knowledge_doc(
    doc_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.query(models.KnowledgeDoc).filter(models.KnowledgeDoc.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    team_id = _get_current_team_id(current_user, db)
    if doc.team_id != team_id:
        raise HTTPException(status_code=403, detail="无权访问该文档")

    db.delete(doc)
    db.commit()
    return {"status": "ok", "message": "已删除"}


@router.get("/knowledge/docs/{doc_id}/versions", response_model=List[schemas.KnowledgeVersionInfo], dependencies=[Depends(require_document)])
def list_knowledge_versions(
    doc_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.query(models.KnowledgeDoc).filter(models.KnowledgeDoc.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    team_id = _get_current_team_id(current_user, db)
    if doc.team_id != team_id:
        raise HTTPException(status_code=403, detail="无权访问该文档")

    versions = (
        db.query(models.KnowledgeVersion)
        .options(joinedload(models.KnowledgeVersion.creator))
        .filter(models.KnowledgeVersion.doc_id == doc_id)
        .order_by(models.KnowledgeVersion.version.desc())
        .all()
    )

    return [schemas.KnowledgeVersionInfo.model_validate(v) for v in versions]


@router.post("/knowledge/docs/{doc_id}/versions", response_model=schemas.KnowledgeVersionInfo, dependencies=[Depends(require_document)])
def create_knowledge_version(
    doc_id: int,
    data: schemas.KnowledgeVersionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.query(models.KnowledgeDoc).filter(models.KnowledgeDoc.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    team_id = _get_current_team_id(current_user, db)
    if doc.team_id != team_id:
        raise HTTPException(status_code=403, detail="无权访问该文档")

    last_version = (
        db.query(models.KnowledgeVersion)
        .filter(models.KnowledgeVersion.doc_id == doc_id)
        .order_by(models.KnowledgeVersion.version.desc())
        .first()
    )
    next_version = (last_version.version + 1) if last_version else 1

    version = models.KnowledgeVersion(
        doc_id=doc_id,
        title=doc.title,
        content=doc.content,
        version=next_version,
        change_summary=data.change_summary,
        created_by=current_user.id,
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    version = (
        db.query(models.KnowledgeVersion)
        .options(joinedload(models.KnowledgeVersion.creator))
        .filter(models.KnowledgeVersion.id == version.id)
        .first()
    )
    return schemas.KnowledgeVersionInfo.model_validate(version)


@router.post("/knowledge/docs/{doc_id}/versions/rollback", response_model=schemas.KnowledgeDocInfo, dependencies=[Depends(require_document)])
def rollback_knowledge_version(
    doc_id: int,
    data: schemas.KnowledgeVersionRollback,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.query(models.KnowledgeDoc).filter(models.KnowledgeDoc.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    team_id = _get_current_team_id(current_user, db)
    if doc.team_id != team_id:
        raise HTTPException(status_code=403, detail="无权访问该文档")

    version = (
        db.query(models.KnowledgeVersion)
        .filter(
            models.KnowledgeVersion.id == data.version_id,
            models.KnowledgeVersion.doc_id == doc_id,
        )
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    doc.title = version.title
    doc.content = version.content
    doc.updated_by = current_user.id
    db.commit()
    db.refresh(doc)

    doc = (
        db.query(models.KnowledgeDoc)
        .options(
            joinedload(models.KnowledgeDoc.creator),
            joinedload(models.KnowledgeDoc.updater),
        )
        .filter(models.KnowledgeDoc.id == doc.id)
        .first()
    )
    return schemas.KnowledgeDocInfo.model_validate(doc)


@router.get("/mindmaps", response_model=List[schemas.MindmapListItem], dependencies=[Depends(require_document)])
def list_mindmaps(
    search: Optional[str] = Query(None, description="搜索关键词"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team_id = _get_current_team_id(current_user, db)
    if not team_id:
        raise HTTPException(status_code=403, detail="您还没有加入任何团队")

    query = (
        db.query(models.Mindmap)
        .options(
            joinedload(models.Mindmap.creator),
            joinedload(models.Mindmap.project),
        )
        .filter(models.Mindmap.team_id == team_id)
    )

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(models.Mindmap.name.ilike(search_pattern))

    if project_id is not None:
        if project_id == 0:
            query = query.filter(models.Mindmap.project_id.is_(None))
        else:
            query = query.filter(models.Mindmap.project_id == project_id)

    maps = query.order_by(models.Mindmap.updated_at.desc()).all()
    return [schemas.MindmapListItem.model_validate(m) for m in maps]


@router.get("/mindmaps/{map_id}", response_model=schemas.MindmapInfo, dependencies=[Depends(require_document)])
def get_mindmap(
    map_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mindmap = (
        db.query(models.Mindmap)
        .options(
            joinedload(models.Mindmap.creator),
            joinedload(models.Mindmap.updater),
        )
        .filter(models.Mindmap.id == map_id)
        .first()
    )
    if not mindmap:
        raise HTTPException(status_code=404, detail="思维导图不存在")

    team_id = _get_current_team_id(current_user, db)
    if mindmap.team_id != team_id:
        raise HTTPException(status_code=403, detail="无权访问该思维导图")

    return schemas.MindmapInfo.model_validate(mindmap)


@router.post("/mindmaps", response_model=schemas.MindmapInfo, dependencies=[Depends(require_document)])
def create_mindmap(
    data: schemas.MindmapCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team_id = _get_current_team_id(current_user, db)
    if not team_id:
        raise HTTPException(status_code=403, detail="您还没有加入任何团队")

    if data.project_id:
        project = db.query(models.Project).filter(models.Project.id == data.project_id).first()
        if not project or project.team_id != team_id:
            raise HTTPException(status_code=404, detail="项目不存在")

    default_content = data.content
    if not default_content:
        root_id = f"root_{int(datetime.utcnow().timestamp() * 1000)}"
        default_content = json.dumps({
            "nodes": {
                root_id: {
                    "id": root_id,
                    "text": data.name,
                    "parentId": None,
                    "children": [],
                    "color": "#2563eb",
                    "textColor": "#ffffff",
                    "x": 2000,
                    "y": 1500,
                    "w": 160,
                    "h": 60,
                    "icon": "",
                    "link": "",
                }
            },
            "rootId": root_id,
            "version": 1,
        })

    mindmap = models.Mindmap(
        team_id=team_id,
        project_id=data.project_id,
        name=data.name,
        content=default_content,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(mindmap)
    db.commit()
    db.refresh(mindmap)

    mindmap = (
        db.query(models.Mindmap)
        .options(
            joinedload(models.Mindmap.creator),
            joinedload(models.Mindmap.updater),
        )
        .filter(models.Mindmap.id == mindmap.id)
        .first()
    )
    return schemas.MindmapInfo.model_validate(mindmap)


@router.put("/mindmaps/{map_id}", response_model=schemas.MindmapInfo, dependencies=[Depends(require_document)])
def update_mindmap(
    map_id: int,
    data: schemas.MindmapUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mindmap = db.query(models.Mindmap).filter(models.Mindmap.id == map_id).first()
    if not mindmap:
        raise HTTPException(status_code=404, detail="思维导图不存在")

    team_id = _get_current_team_id(current_user, db)
    if mindmap.team_id != team_id:
        raise HTTPException(status_code=403, detail="无权访问该思维导图")

    if data.name is not None:
        mindmap.name = data.name
    if data.project_id is not None:
        if data.project_id == 0:
            mindmap.project_id = None
        else:
            project = db.query(models.Project).filter(models.Project.id == data.project_id).first()
            if not project or project.team_id != team_id:
                raise HTTPException(status_code=404, detail="项目不存在")
            mindmap.project_id = data.project_id
    if data.content is not None:
        mindmap.content = data.content
    if data.thumbnail is not None:
        mindmap.thumbnail = data.thumbnail

    mindmap.updated_by = current_user.id
    db.commit()
    db.refresh(mindmap)

    mindmap = (
        db.query(models.Mindmap)
        .options(
            joinedload(models.Mindmap.creator),
            joinedload(models.Mindmap.updater),
        )
        .filter(models.Mindmap.id == mindmap.id)
        .first()
    )
    return schemas.MindmapInfo.model_validate(mindmap)


@router.delete("/mindmaps/{map_id}", dependencies=[Depends(require_document)])
def delete_mindmap(
    map_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mindmap = db.query(models.Mindmap).filter(models.Mindmap.id == map_id).first()
    if not mindmap:
        raise HTTPException(status_code=404, detail="思维导图不存在")

    team_id = _get_current_team_id(current_user, db)
    if mindmap.team_id != team_id:
        raise HTTPException(status_code=403, detail="无权访问该思维导图")

    db.delete(mindmap)
    db.commit()
    return {"status": "ok", "message": "已删除"}


@router.get("/flowcharts", response_model=List[schemas.FlowchartListItem], dependencies=[Depends(require_document)])
def list_flowcharts(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team_id = _get_current_team_id(current_user, db)
    if not team_id:
        raise HTTPException(status_code=403, detail="您还没有加入任何团队")

    charts = (
        db.query(models.Flowchart)
        .options(joinedload(models.Flowchart.creator))
        .filter(models.Flowchart.team_id == team_id)
        .order_by(models.Flowchart.updated_at.desc())
        .all()
    )

    return [schemas.FlowchartListItem.model_validate(c) for c in charts]


@router.get("/flowcharts/{chart_id}", response_model=schemas.FlowchartInfo, dependencies=[Depends(require_document)])
def get_flowchart(
    chart_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chart = (
        db.query(models.Flowchart)
        .options(
            joinedload(models.Flowchart.creator),
            joinedload(models.Flowchart.updater),
        )
        .filter(models.Flowchart.id == chart_id)
        .first()
    )
    if not chart:
        raise HTTPException(status_code=404, detail="流程图不存在")

    team_id = _get_current_team_id(current_user, db)
    if chart.team_id != team_id:
        raise HTTPException(status_code=403, detail="无权访问该流程图")

    return schemas.FlowchartInfo.model_validate(chart)


@router.post("/flowcharts", response_model=schemas.FlowchartInfo, dependencies=[Depends(require_document)])
def create_flowchart(
    data: schemas.FlowchartCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team_id = _get_current_team_id(current_user, db)
    if not team_id:
        raise HTTPException(status_code=403, detail="您还没有加入任何团队")

    chart = models.Flowchart(
        team_id=team_id,
        name=data.name,
        content=data.content,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(chart)
    db.commit()
    db.refresh(chart)

    chart = (
        db.query(models.Flowchart)
        .options(
            joinedload(models.Flowchart.creator),
            joinedload(models.Flowchart.updater),
        )
        .filter(models.Flowchart.id == chart.id)
        .first()
    )
    return schemas.FlowchartInfo.model_validate(chart)


@router.put("/flowcharts/{chart_id}", response_model=schemas.FlowchartInfo, dependencies=[Depends(require_document)])
def update_flowchart(
    chart_id: int,
    data: schemas.FlowchartUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chart = db.query(models.Flowchart).filter(models.Flowchart.id == chart_id).first()
    if not chart:
        raise HTTPException(status_code=404, detail="流程图不存在")

    team_id = _get_current_team_id(current_user, db)
    if chart.team_id != team_id:
        raise HTTPException(status_code=403, detail="无权访问该流程图")

    if data.name is not None:
        chart.name = data.name
    if data.content is not None:
        chart.content = data.content
    if data.thumbnail is not None:
        chart.thumbnail = data.thumbnail

    chart.updated_by = current_user.id
    db.commit()
    db.refresh(chart)

    chart = (
        db.query(models.Flowchart)
        .options(
            joinedload(models.Flowchart.creator),
            joinedload(models.Flowchart.updater),
        )
        .filter(models.Flowchart.id == chart.id)
        .first()
    )
    return schemas.FlowchartInfo.model_validate(chart)


@router.delete("/flowcharts/{chart_id}", dependencies=[Depends(require_document)])
def delete_flowchart(
    chart_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chart = db.query(models.Flowchart).filter(models.Flowchart.id == chart_id).first()
    if not chart:
        raise HTTPException(status_code=404, detail="流程图不存在")

    team_id = _get_current_team_id(current_user, db)
    if chart.team_id != team_id:
        raise HTTPException(status_code=403, detail="无权访问该流程图")

    db.delete(chart)
    db.commit()
    return {"status": "ok", "message": "已删除"}
