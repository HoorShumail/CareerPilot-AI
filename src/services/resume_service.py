from uuid import UUID
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.resume.parser_agent import ResumeParserAgent
from src.agents.resume.structuring_agent import ResumeStructuringAgent
from src.db.repositories.resume_repo import resume_repo, resume_version_repo
from src.infrastructure.storage.resume_storage import ResumeStorage
from src.schemas.resume import ResumeCreate, ResumeVersionCreate, ResumeUpdate


class ResumeService:
    def __init__(self):
        self.parser_agent = ResumeParserAgent()
        self.structuring_agent = ResumeStructuringAgent()
        self.storage = ResumeStorage()

    async def upload_resume(
        self,
        db: AsyncSession,
        user_id: UUID,
        filename: str,
        file_bytes: bytes,
        content_type: str,
    ):
        # Parse resume document
        parsed = self.parser_agent.parse(file_bytes, content_type)

        # Convert extracted text into structured resume data
        structured = self.structuring_agent.structure(parsed)

        # Store original file
        saved_path = self.storage.save_resume_file(
            filename,
            file_bytes,
        )

        # Create resume record
        resume_data = {
            "user_id": user_id,
            "original_filename": filename,
            "file_path": saved_path,
            "file_type": content_type,
            "parsed_content": structured,
        }

        resume = await resume_repo.create(
            db,
            obj_in=ResumeCreate(**resume_data),
        )

        # Create initial resume version
        await self.create_resume_version(
            db,
            ResumeVersionCreate(
                resume_id=resume.id,
                content=structured,
                source_description="Initial upload",
                version_type="upload",
            ),
        )

        # Reload relationship before Pydantic serialization
        await db.refresh(
            resume,
            attribute_names=["versions"],
        )

        return resume

    async def create_resume_version(
        self,
        db: AsyncSession,
        version_in: ResumeVersionCreate,
    ):
        version_data = {
            "resume_id": version_in.resume_id,
            "content": version_in.content,
            "source_description": version_in.source_description,
            "version_type": version_in.version_type,
        }

        return await resume_version_repo.create(
            db,
            obj_in=version_data,
        )

    async def get_user_resumes(
        self,
        db: AsyncSession,
        user_id: UUID,
    ):
        return await resume_repo.get_by_user(
            db,
            user_id=user_id,
        )

    async def get_resume_versions(
        self,
        db: AsyncSession,
        resume_id: UUID,
    ):
        return await resume_version_repo.get_by_resume(
            db,
            resume_id=resume_id,
        )

    async def update_resume(
        self,
        db: AsyncSession,
        resume,
        parsed_content: Dict[str, Any],
    ):
        updated = await resume_repo.update(
            db,
            db_obj=resume,
            obj_in=ResumeUpdate(
                parsed_content=parsed_content
            ),
        )

        await self.create_resume_version(
            db,
            ResumeVersionCreate(
                resume_id=resume.id,
                content=parsed_content,
                source_description="Edited parsed content",
                version_type="manual_edit",
            ),
        )

        # Reload versions after creating new version
        await db.refresh(
            updated,
            attribute_names=["versions"],
        )

        return updated