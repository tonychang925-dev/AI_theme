from datetime import datetime, date, time
from typing import Optional
from pydantic import BaseModel, Field
import hashlib

class NewsRawItem(BaseModel):
    """标准化新闻数据模型"""
    title: str
    content: str
    source: str
    publish_date: date
    publish_time: Optional[time] = None
    market: str = "A股"
    url: Optional[str] = None
    news_id: Optional[str] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        # 自动生成唯一ID
        if not self.news_id:
            self.news_id = self._generate_id()
    
    def _generate_id(self):
        """基于标题和日期生成唯一ID"""
        unique_str = f"{self.title}{self.publish_date}"
        return hashlib.md5(unique_str.encode()).hexdigest()
    
    class Config:
        from_attributes = True