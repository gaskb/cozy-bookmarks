import pytest
from sqlalchemy.exc import IntegrityError

from app.domain.bookmark import Tag, _get_or_create_tags
from app.domain.user import User, hash_password


def test_tag_unique_constraint_enforced_at_db_level(db_session, user):
    tag1 = Tag(user_id=user.id, name="dev")
    db_session.add(tag1)
    db_session.commit()

    tag2 = Tag(user_id=user.id, name="dev")
    db_session.add(tag2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_tag_uniqueness_is_per_user(db_session, user):
    user2 = User(email="other@example.com", password_hash=hash_password("pw"))
    db_session.add(user2)
    db_session.commit()

    tag1 = Tag(user_id=user.id, name="python")
    tag2 = Tag(user_id=user2.id, name="python")
    db_session.add_all([tag1, tag2])
    db_session.commit()

    assert tag1.id != tag2.id
    assert tag1.name == tag2.name


def test_get_or_create_tags_normalizes_and_deduplicates(db_session, user):
    tags = _get_or_create_tags(db_session, user.id, ["Python", "python", "  PYTHON  ", "AI"])
    db_session.commit()

    assert len(tags) == 2
    names = {t.name for t in tags}
    assert names == {"python", "ai"}


def test_get_or_create_tags_handles_concurrency_race(db_session, user):
    from sqlalchemy.orm import sessionmaker
    from app.time_utils import utcnow

    orig_add = db_session.add
    race_triggered = False

    def race_add(instance):
        nonlocal race_triggered
        if isinstance(instance, Tag) and instance.name == "concurrent" and not race_triggered:
            race_triggered = True
            # Simulate a concurrent transaction committing the tag before this transaction flushes
            other_session = sessionmaker(bind=db_session.get_bind())()
            other_session.add(
                Tag(user_id=user.id, name="concurrent", pinned=False, created_at=utcnow())
            )
            other_session.commit()
            other_session.close()
        orig_add(instance)

    db_session.add = race_add
    try:
        tags = _get_or_create_tags(db_session, user.id, ["concurrent"])
        db_session.commit()
        assert len(tags) == 1
        assert tags[0].name == "concurrent"
        assert race_triggered is True
    finally:
        db_session.add = orig_add
