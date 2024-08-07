import os.path as osp
import sys
src_path = osp.normpath(osp.join(osp.join(osp.join(osp.dirname(__file__), '..', '..', 'src'))))
sys.path.append(src_path)

import unittest
import unittest.mock

import env
import dotenv.main

env_path = osp.join(osp.join(osp.join(osp.dirname(__file__), '..'), '..'), '.env')
env.envs = dotenv.main.dotenv_values(env_path)

import sqlalchemy as sqla

from core import procrisk
from core.db import database, model

database.DBPATH = ':memory:'


# Test data

is_checked = True
level = 2
remark = 'testtest'

props = \
{
    'checked': is_checked,
    'level': level,
    'remark': remark,
}


class ProcRiskTest(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        database.init()

    def tearDown(self):
        database.close()

    async def test_create_risk(self):

        rid = await procrisk.create_risk()

        async with database.db_sessionmaker() as db_session:
            query = sqla.select(model.Risk).where(model.Risk.id == rid).limit(1)
            try:
                risk = (await db_session.execute(query)).one()[0]
            except sqla.exc.NoResultFound:
                self.fail("Couldn't find a risk that was supposed to be added.")

    async def test_set_risk(self):
        rid = await procrisk.create_risk()

        await procrisk.set_risk(rid, props)

        async with database.db_sessionmaker() as db_session:
            query = sqla.select(model.Risk).where(model.Risk.id == rid).limit(1)
            try:
                risk = (await db_session.execute(query)).one()[0]
            except sqla.exc.NoResultFound:
                self.fail("Couldn't find a risk that was supposed to be added.")
            else:

                is_checked_ = risk.is_checked
                level_ = risk.level
                reason_genre_ = risk.reason_genre
                remark_ = risk.remark

                self.assertEqual(is_checked, is_checked_, "Couldn't match risk-data 'is_checked'.")
                self.assertEqual(level, level_, "Couldn't match risk-data 'level'.")
                self.assertEqual(None, reason_genre_, "Couldn't match risk-data 'reason_genre'.")
                self.assertEqual(remark, remark_, "Couldn't match risk-data 'remark'.")




