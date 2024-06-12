from functools import cache
from typing import Annotated
from fastapi import Depends, HTTPException,  status, APIRouter
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.routers.auth_utils import get_user_from_token
from .. import models
from ..database import get_db
from ..schemas.postSchemas import  *

router = APIRouter(
    prefix="/posts", # Like Common Factor for these router
    tags=["Posts"] # Dived These End-Points into groups or categories
)



@router.get('')
async def get_all_posts(user: models.User = Depends(get_user_from_token),db: Session = Depends(get_db), page: int = 1, per_page: int = 5) -> PostPaginationResponse:
    skip: int = ( page - 1 ) * per_page
    count = db.query(models.Post.id).count()
    pages_count = count // per_page + (1 if count % per_page else 0) # 32 // 10 = 3 + is still has data ? yes then + 1 : no then + 0 => 4

    posts = db.query(models.Post).limit(per_page).offset(skip).all()
    
    response = {
        "count" : len(posts),
        "page" : page,
        "pages_count": [page for page in range(1, pages_count+1)],
        "posts" : posts
    }
    return response




@router.get('/me')
async def get_all_me_posts(user: models.User = Depends(get_user_from_token), db: Session = Depends(get_db), q: str='', page: int = 1, per_page: int = 5) -> PostPaginationResponse:
    print(q)
    skip: int = ( page - 1 ) * per_page

    count = db.query(models.Post.id).filter(models.Post.user_id == user.id, models.Post.title.contains(q)).count()

    pages_count = count // per_page + (1 if count % per_page else 0)
    posts = db.query(models.Post).filter(models.Post.user_id == user.id, models.Post.title.contains(q)).limit(per_page).offset(skip).all()

    
    response = {
        "count" : len(posts),
        "page" : page,
        "pages_count": [page for page in range(1, pages_count+1)],
        "posts" : posts
    }
    return response




# async def get_posts_time_line(user: Annotated[models.User, Depends(get_user_from_token)], db: Session = Depends(get_db), page: int = 1, per_page: int = 10):  
@router.get('/time-line')
async def get_posts_time_line(user: Annotated[models.User, Depends(get_user_from_token)], db: Session = Depends(get_db), page: int = 1, per_page: int = 10) -> PostsLinePaginator:  
    count: int = db.query(models.Post.id).count()

    if not count:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'no posts')
    
    no_pages = (count // per_page) + (1 if count % per_page != 0 else 0)
    if page > no_pages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'page {page} out of range.')
    
    skip: int = (page - 1) * per_page



# Keys used in pydantic and values for db query
    fields = {
        'post' : models.Post,
        'no_likes': func.count(models.Likes.user_id).label('no_like')
    }
    
    # Fetch Posts
    posts = db.query(*fields.values()) \
            .outerjoin(models.Likes, models.Post.id == models.Likes.post_id) \
            .join(models.User, models.Post.user_id == models.User.id) \
            .group_by(models.Post.id, models.User.id) \
            .order_by(desc(models.Post.created_at)) \
            .limit(per_page) \
            .offset(skip) \
            .all()
    
    # corresponding values of post with fields via zip function, then convert it to dict, then unpack the dict to pass it to PostLine Object Model
    posts_pydantic = [PostLine(**dict(zip(fields.keys(), post))) for post in posts]

    
    return PostsLinePaginator(
        result=posts_pydantic,
        count=count,
        no_pages=no_pages,
        current_page=page, 
        has_next=page != no_pages, 
        has_pre=page > 1)


@router.get('/{id}')
async def get_post(id: int, user: models.User = Depends(get_user_from_token), db: Session = Depends(get_db)) -> PostResponse:
    post : dict | None = db.query(models.Post).get(id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id {id} doesn't exisit")
    return post


@router.post('',status_code=status.HTTP_201_CREATED)
async def create_post(payload: CreatePostSchema, user: models.User = Depends(get_user_from_token), db: Session = Depends(get_db)) -> CreatePostResponseSchema:
    
    new_post = models.Post(**payload.model_dump(),user_id=user.id) # create Object Model
    db.add(new_post) # Do INSERT operation for Object Model
    db.commit() 
    db.refresh(new_post) # like returning, get the inserted post and fill the other values that fill it from DB like id, created_at
    return new_post


@router.patch('/{id}',status_code=status.HTTP_202_ACCEPTED, )
async def update_post(id: int, payload: UpdatePostSchema, user: models.User = Depends(get_user_from_token), db: Session = Depends(get_db)) -> UpdatePostResponseSchema:
    
    post_query = db.query(models.Post).filter(models.Post.id == id) # Store The Query not Execution
    post: models.Post | None = post_query.first() # First Call, [Execution]

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"post with id {id} doesn't exisit")

    if post.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"unauthorized to do this action")
    
    post_query.update({**payload.model_dump()},synchronize_session=False) # Execution Update Query
    db.commit() # Save All Things

    return post



#? NOTE: Response 204 Should Don't Send Data Back, This Is The Mechaneciem Of The 204 Response
@router.delete('/{id}',status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(id: int, user: models.User = Depends(get_user_from_token), db: Session = Depends(get_db)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post: models.Post | None = post_query.first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"post with id {id} doesn't exisit")

    if post.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"unauthorized to do this action")
    

    post_query.delete(synchronize_session=False)
    db.commit()
