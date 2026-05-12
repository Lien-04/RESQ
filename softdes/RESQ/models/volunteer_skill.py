"""
Volunteer Skill Model - SQLAlchemy model for volunteer skills
"""
from ..db import db


class VolunteerSkill(db.Model):
    __tablename__ = 'volunteer_skills'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    proficiency_level = db.Column(db.String(50), default='intermediate')

    user = db.relationship('User', back_populates='skills_entries')

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'skill_name': self.skill_name,
            'proficiency_level': self.proficiency_level
        }
