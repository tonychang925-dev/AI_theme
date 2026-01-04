import os

# 数据库
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost/stock_data"
)

# LLM
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# 题材阈值
THEME_MIN_CONFIDENCE = float(os.getenv("THEME_MIN_CONFIDENCE", 0.4))
