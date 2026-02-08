import os
from sqlalchemy import text
from .config import SRT_DIR
from .db import get_session
from .logging_utils import log_info

def parse_srt_file(filepath: str) -> str:
    # Simple SRT parser: concatenate all text blocks
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    text_blocks = []
    block = []
    for line in lines:
        line = line.strip()
        if line.isdigit() or '-->' in line or not line:
            if block:
                text_blocks.append(' '.join(block))
                block = []
        else:
            block.append(line)
    if block:
        text_blocks.append(' '.join(block))
    return '\n'.join(text_blocks)

def extract_season_episode_from_filename(fname: str):
    # Expecting sXXeYY or SXXEYY in filename
    import re
    m = re.search(r'[sS](\d+)[eE](\d+)', fname)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None

def ingest_transcripts():
    session = get_session()
    processed = inserted = updated = skipped = 0

    for fname in os.listdir(SRT_DIR):
        if fname.endswith('.srt'):
            season, episode = extract_season_episode_from_filename(fname)
            if not season or not episode:
                skipped += 1
                continue

            from .id_maps import get_or_create_episode
            episode_id = get_or_create_episode(season, episode, session)

            # FIX 1: avoid shadowing SQLAlchemy text()
            transcript_text = parse_srt_file(os.path.join(SRT_DIR, fname))

            # Check if transcript exists
            row = session.execute(
                text("SELECT id FROM transcripts "
                     "WHERE episode_id = :episode_id AND source_file = :source_file"),
                {"episode_id": episode_id, "source_file": fname}
            ).fetchone()

            if row:
                session.execute(
                    text("UPDATE transcripts SET text = :text WHERE id = :id"),
                    {"text": transcript_text, "id": row[0]}
                )
                updated += 1
            else:
                # FIX 2: corrected missing parenthesis in VALUES()
                session.execute(
                    text("INSERT INTO transcripts (episode_id, text, source_file) "
                         "VALUES (:episode_id, :text, :source_file)"),
                    {"episode_id": episode_id, "text": transcript_text, "source_file": fname}
                )
                inserted += 1

            processed += 1

    session.commit()
    log_info('ingest_transcripts',
             processed=processed,
             inserted=inserted,
             updated=updated,
             skipped=skipped)
    session.close()
