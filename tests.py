import mock
import unittest

from alfred_db.session import Session
from alfred_db.models import Base, User, Repository, Permission
from alfred_hooks.handlers import HooksHandler

from pretend import stub
from sqlalchemy import create_engine


engine = create_engine('sqlite:///:memory:')
Session.configure(bind=engine)


def create_user():
    user = User(
        login='xobb1t', github_id=1000, github_access_token='access_token',
        name='Dima Kukushkin', apitoken='some api token', email='dima@kukushkin.me',
    )
    session = Session()
    session.add(user)
    session.commit()
    try:
        return user.id
    finally:
        session.close()


def create_repo(user_id):
    repo = Repository(github_id=2000, url='https://github.com/alfredhq/alfred',
                      name='alfred', token='some_special_token', owner_type='user',
                      owner_name='xobb1t', owner_id=1000)
    session = Session()
    session.add(repo)
    session.flush()

    permission = Permission(user_id=user_id, repository_id=repo.id,
                            admin=True)
    session.add(permission)
    session.commit()
    try:
        return repo.id
    finally:
        session.close()


class HooksHandlerTestCase(unittest.TestCase):

    config = {
        'listener_url': 'http://listener.alfredhq.org',
        'database_uri': 'sqlite:///:memory:'
    }

    def setUp(self):
        Base.metadata.create_all(engine)
        self.user_id = create_user()
        self.repo_id = create_repo(self.user_id)
        self.session = Session()
        self.github_patcher = mock.patch('github.Github')
        self.Github = self.github_patcher.start()
        self.github = self.Github.return_value

        self.task = {'user_id': self.user_id, 'repo_id': self.repo_id}
        self.hooks_handler = HooksHandler(self.session, self.config, self.task)
        self.hooks_handler.user = self.session.query(User).get(self.user_id)
        self.hooks_handler.github = self.github

    def tearDown(self):
        self.hooks_handler = None
        self.github_patcher.stop()
        self.session.close()
        Base.metadata.drop_all(engine)

    @mock.patch('alfred_hooks.handlers.HooksHandler.get_github_repo')
    def test_create_hook(self, get_github_repo):
        repo = stub(token='repo-token', hook_id=None)
        hook = stub(id='123321')
        github_repo = mock.Mock()
        get_github_repo.return_value = github_repo
        listener_url = '{}/?token={}'.format(
            self.config['listener_url'],
            repo.token,
        )
        hook_config = {
            'url': listener_url,
            'content_type': 'json'
        }
        github_repo.create_hook.return_value = hook
        self.hooks_handler.create_hook(repo)
        github_repo.create_hook.assert_called_once_with(
            'web', config=hook_config
        )
        self.assertEqual(repo.hook_id, hook.id)

    @mock.patch('alfred_hooks.handlers.HooksHandler.get_github_repo')
    def test_delete_hook(self, get_github_repo):
        repo = stub(token='repo-token', hook_id='123321')
        github_repo = mock.Mock()
        hook = mock.Mock()
        get_github_repo.return_value = github_repo
        github_repo.get_hook.return_value = hook

        self.hooks_handler.delete_hook(repo)
        github_repo.get_hook.assert_called_once_with('123321')
        self.assertTrue(hook.delete.called)
        self.assertIsNone(repo.hook_id)

    def test_get_github_repo(self):
        repo = stub(owner_name='alfredhq', name='alfred')
        repo_owner = mock.Mock()
        github_repo = stub(id=1000)

        self.github.get_user.return_value = repo_owner
        repo_owner.get_repo.return_value = github_repo
        self.assertEqual(self.hooks_handler.get_github_repo(repo), github_repo)
        self.github.get_user.assert_called_once_with('alfredhq')
        repo_owner.get_repo.assert_called_once_with('alfred')

    def test_check_permissions(self):
        has_permissions = self.hooks_handler.check_permissions()
        self.assertTrue(has_permissions)
        self.session.query(Permission).update(
            {'admin': False}, synchronize_session='fetch',
        )
        has_permissions = self.hooks_handler.check_permissions()
        self.assertFalse(has_permissions)

    @mock.patch('alfred_hooks.handlers.HooksHandler.create_hook')
    @mock.patch('alfred_hooks.handlers.HooksHandler.delete_hook')
    @mock.patch('alfred_hooks.handlers.HooksHandler.get_repo')
    def test_run(self, get_repo, delete_hook, create_hook):
        c_repo = stub(id=1000, hook_id=None)
        d_repo = stub(hook_id=2000)
        get_repo.return_value = c_repo
        self.hooks_handler.run()
        get_repo.return_value = d_repo
        self.hooks_handler.run()

        create_hook.assert_called_once_with(c_repo)
        delete_hook.assert_called_once_with(d_repo)

    def test_run_without_user(self):
        self.session.query(User).delete('fetch')
        self.hooks_handler.run()
        self.assertFalse(self.Github.called)
