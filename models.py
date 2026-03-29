from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import text

# Declarative base para definir las clases del ORM
Base = declarative_base()

# Conexión inicial sin base de datos para crearla si no existe (usuario root, sin contraseña)
DATABASE_URL_NO_DB = "mysql+mysqlconnector://root:@localhost/"
engine_no_db = create_engine(DATABASE_URL_NO_DB)

# Crear la base de datos 'test_db' si no existe
def create_database():
    with engine_no_db.connect() as conn:
        conn.execute(text("CREATE DATABASE IF NOT EXISTS lepetit_db"))
        print("Base de datos 'lepetit_db' creada o ya existía.")

# Ahora conectamos a la base de datos creada (usuario root, sin contraseña)
DATABASE_URL_WITH_DB = "mysql+pymysql://root:@localhost/lepetit_db"
engine_with_db = create_engine(DATABASE_URL_WITH_DB)

# Sesión para interactuar con la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_with_db)

# Modelo de la tabla "User" 
class Cliente(Base):
    __tablename__ = "cliente"
    
    idcliente = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    password = Column(String(255))
    correo = Column(String(100), unique=True, nullable=False)
    # Añadimos estos para el Punto 3.3 del taller
    tipo_documento = Column(String(20), nullable=True) 
    numero_documento = Column(String(50), nullable=True)

# Crea la base de datos y las tablas solo si este archivo se ejecuta directamente
if __name__ == "__main__":
    create_database()  # Solo se ejecutará si models.py se corre directamente
    Base.metadata.create_all(bind=engine_with_db)
    print("Tablas creadas exitosamente.")
