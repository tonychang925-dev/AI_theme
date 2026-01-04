from datetime import datetime
from typing import Optional, List, Union, Any
from pydantic import BaseModel, Field, validator
import hashlib

class NewsEvent(BaseModel):
    """结构化事件模型 - 完整修复版"""
    
    # 关键字段
    event_id: Optional[int] = None  # 新增：数据库主键
    news_id: Union[int, str] = Field(..., description="新闻ID")
    event_type: str = Field(..., description="事件类型")
    impact_industries: List[str] = Field(default=[], description="影响的行业数组")
    direction: str = Field(default="neutral", description="方向：利好/利空/中性")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    summary: str = Field(..., description="事件摘要")
    
    # 处理字段
    news_hash_id: Optional[str] = None
    news_db_id: Optional[int] = None
    raw_news_title: Optional[str] = None
    raw_news_content: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    event_uid: Optional[str] = None
    
    @validator('news_id', pre=True)
    def validate_news_id(cls, v):
        """接受字符串或整数"""
        if v is None:
            raise ValueError('news_id不能为空')
        # 如果是字符串且可以转为整数，则转换
        if isinstance(v, str) and v.isdigit():
            return int(v)
        return v
    
    def __init__(self, **data: Any):
        super().__init__(**data)
        
        # 根据news_id类型设置对应字段
        if isinstance(self.news_id, str):
            self.news_hash_id = self.news_id
            # 尝试转换为整数（如果是数字字符串）
            if self.news_id.isdigit():
                self.news_db_id = int(self.news_id)
        elif isinstance(self.news_id, int):
            self.news_db_id = self.news_id
        
        # 生成唯一ID
        if not self.event_uid:
            self.event_uid = self._generate_event_uid()
    
    def _generate_event_uid(self):
        """生成事件唯一标识"""
        id_str = str(self.news_hash_id or self.news_db_id or self.news_id or '')
        unique_str = f"{id_str}{self.event_type}{self.summary[:50]}"
        return hashlib.md5(unique_str.encode()).hexdigest()
    
    @classmethod
    def from_ai_response(cls, news_db_id: int, news_hash_id: str, ai_data: dict, raw_news: dict = None):
        """从AI响应创建事件对象"""
        # 情感分数转方向
        sentiment = ai_data.get('sentiment', 0)
        if sentiment > 0.3:
            direction = "利好"
        elif sentiment < -0.3:
            direction = "利空"
        else:
            direction = "中性"
        
        # 行业处理
        industry = ai_data.get('industry', '通用')
        impact_industries = [industry] if industry and industry != '通用' else []
        
        # 创建对象
        return cls(
            news_id=news_db_id,  # 使用整数ID
            news_hash_id=news_hash_id,
            event_type=ai_data.get('event_type', '未知'),
            impact_industries=impact_industries,
            direction=direction,
            confidence=ai_data.get('confidence', 0.5),
            summary=ai_data.get('summary', ''),
            raw_news_title=raw_news.get('title', '') if raw_news else '',
            raw_news_content=raw_news.get('content', '') if raw_news else '',
            source=raw_news.get('source', '') if raw_news else ''
        )
    
    def to_db_dict(self):
        """转换为数据库格式"""
        # 确定使用哪个ID（优先用整数ID）
        db_news_id = self.news_db_id
        if db_news_id is None and isinstance(self.news_id, int):
            db_news_id = self.news_id
        
        return {
            'event_id': self.event_id,  # 新增
            'news_id': db_news_id,
            'event_type': self.event_type,
            'impact_industries': self.impact_industries,
            'direction': self.direction,
            'confidence': self.confidence,
            'summary': self.summary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'event_uid': self.event_uid
        }
    
    class Config:
        from_attributes = True
        extra = "ignore"  # 忽略额外字段
