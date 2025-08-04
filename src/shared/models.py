from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Asset(Base):
    """Asset model for managing digital assets"""
    __tablename__ = 'assets'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    asset_metadata = Column(JSON)
    tags = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    files = relationship("File", back_populates="asset")
    transcodes = relationship("Transcode", back_populates="asset")


class File(Base):
    """File model for managing file uploads and storage"""
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    checksum = Column(String(64))
    asset_id = Column(Integer, ForeignKey('assets.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    asset = relationship("Asset", back_populates="files")


class Transcode(Base):
    """Transcode model for managing media conversions"""
    __tablename__ = 'transcodes'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'))
    source_format = Column(String(20), nullable=False)
    target_format = Column(String(20), nullable=False)
    output_path = Column(String(500))
    status = Column(String(20), default='pending')  # pending, processing, completed, failed
    progress = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    asset = relationship("Asset", back_populates="transcodes")


class SearchIndex(Base):
    """Search index model for managing search data"""
    __tablename__ = 'search_indices'
    
    id = Column(Integer, primary_key=True)
    entity_type = Column(String(50), nullable=False)  # asset, file, transcode
    entity_id = Column(Integer, nullable=False)
    search_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 