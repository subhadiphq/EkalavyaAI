"""
EkalavyaAI — Database Seed Script
Seeds initial exam structure (chapters, topics) into PostgreSQL.
Run: python -m scripts.seed_data
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import create_tables, get_async_session
from models.user import Chapter, Topic, ExamType

CA_FOUNDATION_CHAPTERS = [
    ("Principles and Practice of Accounting", [
        ("Theoretical Framework", 0.8), ("Accounting Process", 0.9),
        ("Bank Reconciliation Statement", 0.85), ("Inventories", 0.8),
        ("Depreciation", 0.85), ("Bills of Exchange", 0.75),
        ("Partnership Accounts", 0.95), ("Company Accounts", 0.9),
    ]),
    ("Business Mathematics", [
        ("Ratio and Proportion", 0.7), ("Indices and Logarithm", 0.65),
        ("Equations", 0.8), ("Linear Inequalities", 0.7),
        ("Mathematics of Finance", 0.85), ("Permutations and Combinations", 0.75),
        ("Sets, Relations and Functions", 0.7),
    ]),
    ("Business Economics", [
        ("Introduction to Business Economics", 0.6), ("Theory of Demand and Supply", 0.85),
        ("Theory of Production and Cost", 0.8), ("Price Determination", 0.75),
        ("Business Cycles", 0.7), ("Determination of National Income", 0.75),
        ("Public Finance", 0.7), ("Money Market", 0.7),
    ]),
    ("Business and Commercial Knowledge", [
        ("Introduction to Business", 0.6), ("Business Environment", 0.7),
        ("Business Organizations", 0.75), ("Government Policies", 0.65),
        ("Important Organisations", 0.6),
    ]),
]

JEE_CHAPTERS = [
    ("Physics", [
        ("Kinematics", 0.9), ("Laws of Motion", 0.95), ("Work, Energy, Power", 0.9),
        ("Rotational Motion", 0.85), ("Gravitation", 0.8), ("Thermodynamics", 0.9),
        ("Electrostatics", 0.95), ("Current Electricity", 0.95), ("Magnetic Effects", 0.9),
        ("Electromagnetic Induction", 0.9), ("Optics", 0.85), ("Modern Physics", 0.9),
    ]),
    ("Chemistry", [
        ("Some Basic Concepts", 0.8), ("Atomic Structure", 0.85), ("Chemical Bonding", 0.9),
        ("Thermodynamics", 0.85), ("Equilibrium", 0.9), ("Redox Reactions", 0.8),
        ("Organic Chemistry Basics", 0.9), ("Hydrocarbons", 0.85),
        ("Coordination Compounds", 0.85), ("Electrochemistry", 0.9),
    ]),
    ("Mathematics", [
        ("Sets and Functions", 0.75), ("Algebra", 0.9), ("Coordinate Geometry", 0.9),
        ("Calculus - Limits", 0.9), ("Calculus - Derivatives", 0.95),
        ("Calculus - Integrals", 0.95), ("Vectors and 3D", 0.9),
        ("Probability", 0.85), ("Matrices and Determinants", 0.85),
    ]),
]

NEET_CHAPTERS = [
    ("Physics", [
        ("Physical World and Units", 0.7), ("Kinematics", 0.85), ("Laws of Motion", 0.9),
        ("Work, Energy, Power", 0.85), ("Gravitation", 0.8), ("Properties of Matter", 0.75),
        ("Thermodynamics", 0.85), ("Current Electricity", 0.9), ("Magnetism", 0.85),
        ("Optics", 0.9), ("Modern Physics", 0.95),
    ]),
    ("Chemistry", [
        ("Basic Concepts", 0.8), ("Structure of Atom", 0.85), ("Periodic Table", 0.85),
        ("Chemical Bonding", 0.9), ("States of Matter", 0.8), ("Thermodynamics", 0.85),
        ("Equilibrium", 0.85), ("Biomolecules", 0.9), ("Polymers", 0.8),
        ("Environmental Chemistry", 0.7),
    ]),
    ("Biology", [
        ("Cell Biology", 0.95), ("Cell Division", 0.95), ("Plant Kingdom", 0.85),
        ("Animal Kingdom", 0.9), ("Morphology of Plants", 0.85), ("Anatomy of Plants", 0.8),
        ("Structural Organisation of Animals", 0.85), ("Digestion and Absorption", 0.9),
        ("Breathing and Gas Exchange", 0.9), ("Body Fluids and Circulation", 0.9),
        ("Excretory Products", 0.85), ("Locomotion and Movement", 0.8),
        ("Neural Control", 0.9), ("Chemical Coordination", 0.85),
        ("Reproduction in Plants", 0.9), ("Human Reproduction", 0.95),
        ("Genetics and Evolution", 0.95), ("Human Health and Disease", 0.9),
        ("Ecosystem", 0.85), ("Biodiversity", 0.8),
    ]),
]


async def seed_exam(exam_type: ExamType, chapters_data: list):
    """Seed chapters and topics for an exam."""
    async with get_async_session() as session:
        chapter_no = 1
        total_chapters = 0
        total_topics = 0

        for subject, topics_data in chapters_data:
            chapter = Chapter(
                exam=exam_type,
                subject=subject,
                chapter_no=chapter_no,
                name=subject,
                importance_score=0.8,
                pyq_frequency=5,
                total_topics=len(topics_data),
            )
            session.add(chapter)
            await session.flush()

            for i, (topic_name, importance) in enumerate(topics_data, 1):
                topic = Topic(
                    chapter_id=chapter.id,
                    name=topic_name,
                    importance_score=importance,
                    pyq_frequency=int(importance * 8),
                )
                session.add(topic)
                total_topics += 1

            chapter_no += 1
            total_chapters += 1

        await session.commit()
        print(f"  ✅ {exam_type.value}: {total_chapters} chapters, {total_topics} topics")


async def main():
    print("🌱 EkalavyaAI Database Seeding...")
    await create_tables()
    print("✅ Tables created")

    print("Seeding exam structures:")
    await seed_exam(ExamType.CA_FOUNDATION, CA_FOUNDATION_CHAPTERS)
    await seed_exam(ExamType.JEE, JEE_CHAPTERS)
    await seed_exam(ExamType.NEET, NEET_CHAPTERS)

    print("\n✅ Seeding complete! Ready to run EkalavyaAI.")


if __name__ == "__main__":
    asyncio.run(main())
