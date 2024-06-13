from datetime import datetime
from pydantic import BaseModel, field_validator
from . import userSchemas
from typing import List


# REQUEST Validator

class BasePostSchema(BaseModel):
    title: str # required Field
    content: str # required Field
    # created_at: datetime
    published: bool = True # has default value


    # Custom Validation
    @field_validator('title')
    def title_validator(cls,value):
        if len(value) < 4:
            raise ValueError("Title Should Be More Than 7 Letter")
        
        return value
    
    class Config:
        from_attributes = True
    
class CreatePostSchema(BasePostSchema):
    pass

class CreatePostResponseSchema(BasePostSchema):
    id: int
    user_id: int

class UpdatePostSchema(BasePostSchema):
    pass

class UpdatePostResponseSchema(BasePostSchema):
    id: int
    user_id: int



class PostResponse(BasePostSchema):
    id: int
    user: userSchemas.UserResponse

class PostLine(BaseModel):
    post: PostResponse
    no_likes: int


class PostsLinePaginator(BaseModel):
    count: int
    current_page: int
    has_next: bool
    has_pre: bool
    no_pages: int
    result: List[PostLine]


    class Config:
        from_attributes = True
