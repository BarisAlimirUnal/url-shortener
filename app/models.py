# app/models.py
from datetime import datetime
from app import db


class URL(db.Model):
    """
    Represents one shortened URL in the database.

    Table name: urls
    Columns:
        short_code  — the unique 6-character code (e.g. 'aB3xZ9')
        long_url    — the original full URL
        created_at  — when it was created
        click_count — how many times it has been visited
    """
    __tablename__ = 'urls'

    short_code = db.Column(db.String(10), primary_key=True)
    long_url = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    click_count = db.Column(db.Integer, default=0)

    def to_dict(self):
        """Converts this object to a dictionary for JSON responses"""
        return {
            'short_code': self.short_code,
            'long_url': self.long_url,
            'created_at': self.created_at.isoformat(),
            'click_count': self.click_count
        }