from datetime import datetime, date, timezone, timedelta

# 北京时间 = UTC+8
BEIJING_TZ = timezone(timedelta(hours=8))


def now_bj() -> datetime:
    """当前北京时间（带时区）"""
    return datetime.now(BEIJING_TZ)


def today_bj() -> date:
    """当前北京日期"""
    return now_bj().date()


def naive_now_bj() -> datetime:
    """当前北京时间（去掉时区，用于和数据库里的 naive 字段比较）"""
    return now_bj().replace(tzinfo=None)
