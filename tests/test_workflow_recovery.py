"""Restart recovery closes real edit operations without discarding accepted slides."""
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import repository
from app.db import Base
from app.project_schemas import ProjectCreateRequest, DesignPlan
from app.services import modular_recovery, modular_build
from app.services.outline_service import starter_outline
from app.services.modular_build import build_slide_from_outline


class WorkflowRecoveryTest(unittest.TestCase):
    def test_ready_deck_group_and_block_operations_close_after_restart_keep_accepted_designs(self):
        with tempfile.TemporaryDirectory() as directory:
            engine=create_engine(f"sqlite:///{Path(directory)/'recovery.db'}")
            Base.metadata.create_all(engine);sessions=sessionmaker(bind=engine)
            with sessions() as session:
                project=repository.create_project(session,ProjectCreateRequest(assignment_text='Five slides',context_pack_text='Thesis: accepted content.'))
                outline=starter_outline(project.context_pack_text)
                project.outline_json=[row.model_dump() for row in outline]
                rows=[build_slide_from_outline(row).model_dump() for row in outline]
                for row in rows:
                    row.update(design=DesignPlan(layout='editorial',emphasis='quiet',rationale='Accepted design.').model_dump(),design_status='ready')
                original=deepcopy(rows)
                rows[0]['sections_status']='generating';rows[1]['blocks']['body']['status']='generating'
                project.slides_json=rows;project.phase='ready';project_id=project.id
                project.workflow_json={'stage':'complete','actions':[
                    {'sequence':1,'action':'group_sections','status':'running','slide_id':'s1','detail':''},
                    {'sequence':2,'action':'revise_block','status':'running','slide_id':'s2','detail':''},
                    {'sequence':3,'action':'review_deck','status':'complete','slide_id':None,'detail':''}]};session.commit()
            with patch.object(modular_recovery,'SessionLocal',sessions),patch.object(modular_build,'SessionLocal',sessions):
                modular_recovery.recover_interrupted_work()
            with sessions() as session:
                current=repository.get_project(session,project_id)
                self.assertEqual(current.phase,'ready')
                self.assertEqual([a['status'] for a in current.workflow_json['actions']],['error','error','complete'])
                self.assertEqual(current.slides_json[0]['sections_status'],'error')
                self.assertEqual(current.slides_json[1]['blocks']['body']['status'],'error')
                self.assertEqual([r['blocks']['body']['text'] for r in current.slides_json],[r['blocks']['body']['text'] for r in original])
                self.assertEqual([r['design'] for r in current.slides_json],[r['design'] for r in original])
                self.assertTrue(all(r['design_status']=='ready' for r in current.slides_json))
            engine.dispose()
