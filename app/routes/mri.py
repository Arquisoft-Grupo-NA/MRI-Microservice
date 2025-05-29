from fastapi import APIRouter, Depends, Request, Query, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from app import crud, schemas
from app.templates import templates
from app.auth import get_current_user
from datetime import date # Importar date para manejar fechas

router = APIRouter()
ALLOWED_ROLES = ['missanoguga', 'sebastianmartinezarias','sebasmar2015']

def check_role(user):
    role = user["userinfo"].get("nickname")
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail=f"Unauthorized User: role is '{role}'")

@router.get("/", response_class=HTMLResponse)
async def mri_list_html(
    request: Request,
    page: int = Query(1, ge=1),
    fecha_inicio: date = Query(None), # Nuevo parámetro de consulta
    fecha_fin: date = Query(None),    # Nuevo parámetro de consulta
    user=Depends(get_current_user),
):
    check_role(user)
    limit = 10
    skip = (page - 1) * limit
    mris = await crud.get_mris_by_user(
        user["userinfo"]["sub"],
        skip=skip,
        limit=limit,
        fecha_inicio=fecha_inicio, # Pasar los parámetros de fecha al crud
        fecha_fin=fecha_fin
    )
    pagination = {"page": page, "total_pages": 10, "has_previous": page > 1, "has_next": True}
    return templates.TemplateResponse(
        "mri_list.html",
        {
            "request": request,
            "mris": mris,
            "pagination": pagination,
            "fecha_inicio": fecha_inicio.isoformat() if fecha_inicio else "", # Pasar al template
            "fecha_fin": fecha_fin.isoformat() if fecha_fin else ""           # Pasar al template
        }
    )

@router.get("/create", response_class=HTMLResponse)
async def mri_create_form(request: Request, user=Depends(get_current_user)):
    check_role(user)
    return templates.TemplateResponse("mri_create.html", {"request": request, "errors": []})

@router.post("/create", response_class=HTMLResponse)
async def mri_create_post(
    request: Request,
    fecha: str = Form(...),
    hora: str = Form(...),
    descripcion: str = Form(...),
    paciente_id: str = Form(...),
    user=Depends(get_current_user),
):
    check_role(user)
    errors = []
    try:
        data = schemas.MRICreate(fecha=fecha, hora=hora, descripcion=descripcion, paciente_id=paciente_id)
        await crud.create_mri(data, user["userinfo"]["sub"])
        return RedirectResponse(url="/mri/", status_code=HTTP_303_SEE_OTHER)
    except Exception as e:
        errors.append(str(e))
        return templates.TemplateResponse("mri_create.html", {"request": request, "errors": errors})