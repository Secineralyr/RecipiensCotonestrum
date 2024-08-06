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

from core import procemoji
from core.db import database, model

database.DBPATH = ':memory:'


# Test data

data = \
[
    {
        'misskey_id': '9wj3hos4zmd60008',
        'name': 'emoji_name1',
        'category': 'emoji_category1',
        'tags': 'tag1 tag2',
        'url': 'https://<domain.misskey.com>/files/e457b866-d84c-42d9-b006-d70480a08c88',
        'is_self_made': True,
        'license': 'Created by tester',

        'created_at': '2024-01-01T00:00:00.000Z',
        'updated_at': '2024-01-01T00:00:01.000Z',

        'user_id': '9wj3fm8izmd60001',
        'user_name': 'tester',
    },
    {
        'misskey_id': '9wj3hos4zmd60009',
        'name': 'emoji_name2',
        'category': 'emoji_category2',
        'tags': 'tag3 tag4',
        'url': 'https://<domain.misskey.com>/files/18f0574e-6d51-40d1-8553-c6ba144f8626',
        'is_self_made': False,
        'license': 'Test data',

        'created_at': '2024-01-01T00:00:05.000Z',
        'updated_at': '2024-01-01T00:00:07.000Z',

        'user_id': '9wj3fm8izmd60001',
        'user_name': 'tester',
    },
]


data_user = \
[
    {
        'id': data0['user_id'],
        'name': None,
        'username': data0['user_name'],
        'host': None,
        'createdAt': '1970-01-01T00:00:00.000Z',
        'avatarUrl': 'https://<domain.misskey.com>/identicon/tester@<domain.misskey.com>',
        'avatarBlurhash': None,
        'avatarDecorations': [],
        'isBot': False,
        'isCat': False,
        'emojis': {},
        'onlineStatus': 'online',
        'badgeRoles': [],
    }
    for data0 in data
]

data_emoji = \
[
    {
        'id': data0['misskey_id'],
        'aliases': data0['tags'].split(' '),
        'name': data0['name'],
        'category': data0['category'],
        'host': None,
        'url': data0['url'],
        'isSelfMadeResource': data0['is_self_made'],
        'license': data0['license'],
        'isSensitive': False,
        'localOnly': False,
        'roleIdsThatCanBeUsedThisEmojiAsReaction': [],
        'userId': data0['user_id'],
        'user': data_user0,
    }
    for data0, data_user0 in zip(data, data_user)
]

data_emoji_log = \
[
    [
        {
            'id': 'testlog1',
            'createDate': data0['created_at'],
            'userId': data0['user_id'],
            'user': data_user0,
            'type': 'Add',
            'changesProperties': [],
        },
        {
            'id': 'testlog2',
            'createDate': data0['updated_at'],
            'userId': data0['user_id'],
            'user': data_user0,
            'type': 'Update',
            'changesProperties': [
                {
                    'type': 'category',
                    'changeInfo': {
                        'after': 'catttta',
                        'before': 'catttt',
                    },
                },
            ],
        },
    ]
    for data0, data_user0 in zip(data, data_user)
]


class ProcEmojiTest(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        database.init()

    def tearDown(self):
        database.close()

    async def test_update_emoji(self):

        misskey_id = data[0]['misskey_id']
        name = data[0]['name']
        category = data[0]['category']
        tags = data[0]['tags']
        url = data[0]['url']
        is_self_made = data[0]['is_self_made']
        license = data[0]['license']
        created_at = data[0]['created_at']
        updated_at = data[0]['updated_at']
        user_id = data[0]['user_id']
        user_name = data[0]['user_name']

        with unittest.mock.patch('misskey.miapi.get_emoji_log') as mock_get_emoji_log:
            mock_get_emoji_log.return_value = data_emoji_log[0]

            eid = await procemoji.update_emoji(data_emoji[0])

        async with database.db_sessionmaker() as db_session:
            query = sqla.select(model.Emoji, model.User).outerjoin(model.User, model.Emoji.user_id == model.User.id).where(model.Emoji.id == eid).limit(1)
            try:
                emoji, user = (await db_session.execute(query)).one()
            except sqla.exc.NoResultFound:
                self.fail("Couldn't find an emoji that was supposed to be added.")
            else:
                eid_ = emoji.id
                misskey_id_ = emoji.misskey_id
                name_ = emoji.name
                category_ = emoji.category
                tags_ = emoji.tags
                url_ = emoji.url
                is_self_made_ = emoji.is_self_made
                license_ = emoji.license

                created_at_ = emoji.created_at
                updated_at_ = emoji.updated_at

                user_id_ = user.misskey_id
                user_name_ = user.username

                self.assertEqual(eid, eid_, "Couldn't match emoji-data 'id'.")
                self.assertEqual(misskey_id, misskey_id_, "Couldn't match emoji-data 'misskey_id'.")
                self.assertEqual(name, name_, "Couldn't match emoji-data 'name'.")
                self.assertEqual(category, category_, "Couldn't match emoji-data 'category'.")
                self.assertEqual(tags, tags_, "Couldn't match emoji-data 'tags'.")
                self.assertEqual(url, url_, "Couldn't match emoji-data 'url'.")
                self.assertEqual(is_self_made, is_self_made_, "Couldn't match emoji-data 'is_self_made'.")
                self.assertEqual(license, license_, "Couldn't match emoji-data 'license'.")

                self.assertEqual(created_at, created_at_, "Couldn't match emoji-data 'created_at'.")
                self.assertEqual(updated_at, updated_at_, "Couldn't match emoji-data 'updated_at'.")

                self.assertEqual(user_id, user_id_, "Couldn't match user-data 'misskey_id'.")
                self.assertEqual(user_name, user_name_, "Couldn't match user-data 'username'.")

    async def test_delete_emoji(self):

        misskey_id = data[0]['misskey_id']

        with unittest.mock.patch('misskey.miapi.get_emoji_log') as mock_get_emoji_log:
            mock_get_emoji_log.return_value = data_emoji_log[0]

            eid = await procemoji.update_emoji(data_emoji[0])

        await procemoji.delete_emoji(data_emoji[0])

        async with database.db_sessionmaker() as db_session:
            query = sqla.select(model.Emoji).where(model.Emoji.misskey_id == misskey_id).limit(1)
            with self.assertRaises(sqla.exc.NoResultFound, msg="Found an emoji that was supposed to be deleted."):
                emoji = (await db_session.execute(query)).one()[0]

    async def test_plune_emoji(self):

        misskey_id0 = data[0]['misskey_id']
        misskey_id1 = data[1]['misskey_id']

        with unittest.mock.patch('misskey.miapi.get_emoji_log') as mock_get_emoji_log:
            for i in range(len(data_emoji)):
                mock_get_emoji_log.return_value = data_emoji_log[i]

                eid = await procemoji.update_emoji(data_emoji[i])

        await procemoji.plune_emoji([misskey_id1])

        async with database.db_sessionmaker() as db_session:
            query = sqla.select(model.Emoji).where(model.Emoji.misskey_id == misskey_id0).limit(1)
            with self.assertRaises(sqla.exc.NoResultFound, msg="Found an emoji that was supposed to be pluned."):
                emoji = (await db_session.execute(query)).one()[0]
            
            query = sqla.select(model.Emoji).where(model.Emoji.misskey_id == misskey_id1).limit(1)
            try:
                emoji = (await db_session.execute(query)).one()[0]
            except sqla.exc.NoResultFound:
                self.fail("Couldn't find an emoji that was supposed to be added.")


