from app import app, db, User
from sqlalchemy import text

def add_profile_picture_column():
    """Add profile_picture column to User table"""
    with app.app_context():
        try:
            # Use the newer SQLAlchemy syntax with text() wrapper
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE user ADD COLUMN profile_picture VARCHAR(200) DEFAULT "default.png"'))
                conn.commit()
            print('✓ Added profile_picture column successfully')
        except Exception as e:
            if 'duplicate column name' in str(e).lower() or 'already exists' in str(e).lower():
                print('✓ Profile picture column already exists')
            else:
                print(f'✗ Error adding profile_picture column: {e}')
                # Try to create all tables if there's an issue
                try:
                    db.create_all()
                    print('✓ Created all tables')
                except Exception as create_error:
                    print(f'✗ Error creating tables: {create_error}')

if __name__ == '__main__':
    add_profile_picture_column()
