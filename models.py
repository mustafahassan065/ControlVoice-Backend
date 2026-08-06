from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    plan = Column(String, default="free")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    recordings = relationship("Recording", back_populates="user")

class Recording(Base):
    __tablename__ = "recordings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    audio_url = Column(String, nullable=False)
    transcript = Column(Text, nullable=True)
    acoustic_data = Column(Text, nullable=True)
    duration = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="recordings")
    report = relationship("Report", back_populates="recording", uselist=False)

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recording_id = Column(Integer, ForeignKey("recordings.id"), nullable=False)
    authority_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    presence_score = Column(Float, nullable=True)
    leadership_score = Column(Float, nullable=True)
    pace_score = Column(Float, nullable=True)
    pause_score = Column(Float, nullable=True)
    pitch_score = Column(Float, nullable=True)
    ending_score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    recording = relationship("Recording", back_populates="report")

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    instruction = Column(Text, nullable=False)
    wrong_audio_url = Column(String, nullable=True)
    correct_audio_url = Column(String, nullable=True)
    practice_template = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Program(Base):
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    duration_days = Column(Integer, default=30)
    focus = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_programs = relationship("UserProgram", back_populates="program")


class UserProgram(Base):
    __tablename__ = "user_programs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False)
    current_day = Column(Integer, default=1)
    status = Column(String, default="active")  # active, completed, paused
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    program = relationship("Program", back_populates="user_programs")
class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email_type = Column(String, nullable=False)  # daily_exercise, weekly_progress, test
    email_subject = Column(String, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="sent")  # sent, failed
    resend_id = Column(String, nullable=True)
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    plan = Column(String, default="free")  # free, pro, executive
    status = Column(String, default="active")  # active, canceled, past_due
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
class ProgressSnapshot(Base):
    __tablename__ = "progress_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    authority_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    presence_score = Column(Float, nullable=True)
    leadership_score = Column(Float, nullable=True)
    recording_date = Column(DateTime(timezone=True), server_default=func.now())

class DailyChallenge(Base):
    __tablename__ = "daily_challenges"

    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    date = Column(String, nullable=False)  # YYYY-MM-DD
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserDailyChallenge(Base):
    __tablename__ = "user_daily_challenges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    challenge_id = Column(Integer, ForeignKey("daily_challenges.id"), nullable=False)
    recording_id = Column(Integer, ForeignKey("recordings.id"), nullable=True)
    completed = Column(Integer, default=0)  # 0 = not done, 1 = done
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserXP(Base):
    __tablename__ = "user_xp"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    total_xp = Column(Integer, default=0)
    current_level = Column(Integer, default=1)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class StreakLog(Base):
    __tablename__ = "streak_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_date = Column(String, nullable=False)  # YYYY-MM-DD
    activity_type = Column(String, nullable=False)  # challenge, exercise, assessment
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PersonalBest(Base):
    __tablename__ = "personal_bests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    metric = Column(String, nullable=False)  # authority, confidence, presence, leadership
    previous_best = Column(Float, nullable=True)
    new_best = Column(Float, nullable=False)
    recording_id = Column(Integer, ForeignKey("recordings.id"), nullable=True)
    achieved_at = Column(DateTime(timezone=True), server_default=func.now())

class CoachConversation(Base):
    __tablename__ = "coach_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    messages = Column(Text, nullable=False, default="[]")  # JSON array
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CoachQuestion(Base):
    __tablename__ = "coach_questions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_date = Column(String, nullable=False)  # YYYY-MM-DD
    count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EmailPreference(Base):
    __tablename__ = "email_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    weekly_reports = Column(Integer, default=1)
    practice_reminders = Column(Integer, default=1)
    achievement_emails = Column(Integer, default=1)
    assessment_complete = Column(Integer, default=1)
    product_updates  = Column(Integer, default=1)
    marketing_emails = Column(Integer, default=1)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())