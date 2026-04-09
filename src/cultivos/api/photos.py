"""Field photo upload and analysis endpoints."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from cultivos.db.models import Farm, Field, FieldPhoto
from cultivos.db.session import get_db
from cultivos.models.photo import PhotoAnalysis, PhotoOut
from cultivos.services.crop.photo_analysis import analyze_crop_photo

router = APIRouter(prefix="/api/farms/{farm_id}/fields/{field_id}/photos", tags=["photos"])


def _get_field(farm_id: int, field_id: int, db: Session) -> Field:
    """Validate both farm and field exist, return field."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    field = db.query(Field).filter(Field.id == field_id, Field.farm_id == farm_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.post("", status_code=201)
def upload_photo(
    farm_id: int,
    field_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
):
    """Upload a crop photo and get instant analysis (color histogram, classification)."""
    field = _get_field(farm_id, field_id, db)

    image_bytes = file.file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        analysis = analyze_crop_photo(image_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    photo = FieldPhoto(
        field_id=field.id,
        filename=file.filename or "unnamed",
        content_type=file.content_type or "image/jpeg",
        size_bytes=len(image_bytes),
        analysis_json=analysis,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)

    return _photo_to_out(photo)


@router.get("")
def list_photos(
    farm_id: int,
    field_id: int,
    db: Session = Depends(get_db),
):
    """List all photos for a field, most recent first."""
    _get_field(farm_id, field_id, db)
    photos = (
        db.query(FieldPhoto)
        .filter(FieldPhoto.field_id == field_id)
        .order_by(FieldPhoto.uploaded_at.desc())
        .all()
    )
    return [_photo_to_out(p) for p in photos]


@router.delete("/{photo_id}", status_code=204)
def delete_photo(
    farm_id: int,
    field_id: int,
    photo_id: int,
    db: Session = Depends(get_db),
):
    """Delete a photo record."""
    _get_field(farm_id, field_id, db)
    photo = db.query(FieldPhoto).filter(FieldPhoto.id == photo_id, FieldPhoto.field_id == field_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    db.delete(photo)
    db.commit()


def _photo_to_out(photo: FieldPhoto) -> dict:
    """Convert ORM photo to output dict."""
    analysis = None
    if photo.analysis_json:
        analysis = PhotoAnalysis(**photo.analysis_json)
    return PhotoOut(
        id=photo.id,
        field_id=photo.field_id,
        filename=photo.filename,
        content_type=photo.content_type,
        size_bytes=photo.size_bytes,
        uploaded_at=photo.uploaded_at,
        analysis=analysis,
    ).model_dump(mode="json")
