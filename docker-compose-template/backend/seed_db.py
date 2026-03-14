from base import Base, SessionLocal, User, engine

Base.metadata.create_all(bind=engine)

db = SessionLocal()

existing = db.query(User).filter(User.login.in_(['pavel', 'yura'])).all()
existing_logins = {u.login for u in existing}

users = [
    User(login='pavel', email='a@gmail.com', hashed_password=''),
    User(login='yura', email='b@gmail.com', hashed_password=''),
]

for user in users:
    if user.login not in existing_logins:
        db.add(user)

db.commit()
db.close()
print("Seed complete")
