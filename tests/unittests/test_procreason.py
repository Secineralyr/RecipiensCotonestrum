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

from core import procreason
from core.db import database, model

database.DBPATH = ':memory:'


# Test data
text0 = 'testtesttest'
text1 = 'testtesttestaaa'

class ProcReasonTest(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        database.init()

    def tearDown(self):
        database.close()

    async def test_create_reason(self):

        rsid = await procreason.create_reason(text0)

        async with database.db_sessionmaker() as db_session:
            query = sqla.select(model.Reason).where(model.Reason.id == rsid).limit(1)
            try:
                reason = (await db_session.execute(query)).one()[0]
            except sqla.exc.NoResultFound:
                self.fail("Couldn't find a reason that was supposed to be added.")
            else:
                text_ = reason.reason

                self.assertEqual(text0, text_, "Couldn't match reason-data 'text'.")

    async def test_edit_reason(self):
        rsid = await procreason.create_reason(text0)

        await procreason.edit_reason(rsid, text1)

        async with database.db_sessionmaker() as db_session:
            query = sqla.select(model.Reason).where(model.Reason.id == rsid).limit(1)
            try:
                reason = (await db_session.execute(query)).one()[0]
            except sqla.exc.NoResultFound:
                self.fail("Couldn't find a reason that was supposed to be added.")
            else:

                text_ = reason.reason

                self.assertEqual(text1, text_, "Couldn't match reason-data 'text'.")




