from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.routers.auth_utils import get_user_from_token


router = APIRouter(prefix="/likes", tags=["Likes"])

class Like(BaseModel):
    post_id: int
    type_click: bool

# payload -> post_id + delete or make like
@router.post("", status_code=status.HTTP_201_CREATED)
async def like(payload: Like, user: models.User = Depends(get_user_from_token), db: Session = Depends(get_db)):
    
    # is Post There ?
    if not db.query(models.Post).filter(models.Post.id == payload.post_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with in id {payload.post_id} doesn't exisit")
    
    post = db.query(models.Likes).filter(models.Likes.post_id == payload.post_id, models.Likes.user_id == user.id)
    

    if payload.type_click: # do like
        if post.first(): # is doing like before ?
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"user {user.id} is already liked on the post {payload.post_id}")
        
        # apply like on the post
        like_query = models.Likes(post_id=payload.post_id, user_id=user.id)
        db.add(like_query)
        db.commit()
        return {"message" : "Successfully Liked in the post"}


    if not post.first(): # is liked before in the post ?
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user {user.id} not liked on the post {payload.post_id} before")
    
    # delete like from the post
    post.delete(synchronize_session=False)
    db.commit()
    return {"message" : "Successfully deleted Like"}
    
    
