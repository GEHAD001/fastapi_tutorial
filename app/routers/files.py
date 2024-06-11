import random
from fastapi import Depends, HTTPException,  status, APIRouter, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.config import UPLOAD_DIR

from .. import models
from ..database import get_db


from pathlib import Path


router = APIRouter(
    prefix="/files",
    tags=["Files"]
)

def cutter_file(file: str):
    """
    Splits the filename into the name and extension.
    Raises an exception if the file format is incorrect.
    """
    if file.count('.') != 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File format not correct, should be a single '.'")
    file_name, file_ext = file.split('.')
    return file_name, f'.{file_ext}'


@router.post("/uploadfile/")
async def upload_file(uploaded_file: UploadFile, db: Session = Depends(get_db)):
    file_content = await uploaded_file.read()

    file_name, file_ext = cutter_file(uploaded_file.filename)

    save_to = UPLOAD_DIR / f"{file_name}{file_ext}"

    # Simple Condtion
    if save_to.exists():
        save_to = UPLOAD_DIR / f"{file_name}_{random.randint(0, 15000)}{file_ext}"
        
        
    with open(save_to, 'wb') as file:
        file.write(file_content)
    
    db_file = models.File(
        filename=f'{file_name}{file_ext}',
        dir=str(save_to)
    )
    
    db.add(db_file)
    db.commit()

    return {"message": "Upload successful", "file_id": db_file.id}

@router.get("/{file_id}")
async def get_file(file_id: int, db: Session = Depends(get_db)):
    """
    Downloads a file by its ID.
    """
    db_file = db.query(models.File).filter(models.File.id == file_id).first()

    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = Path(db_file.dir)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(file_path, headers={"Content-Disposition": f"attachment; filename={db_file.filename}", "Content-Type": "application/octet-stream"})