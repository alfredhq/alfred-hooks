from alfred_db.session import Session
from alfred_db.models import User, Repository, Permission

from github import Github

from sqlalchemy import create_engine


class HooksHandler(object):

    @classmethod
    def dispatch(cls, config, task):
        engine = create_engine(config['database_uri'])
        session = Session(bind=engine)
        instance = cls(session, config, task)
        try:
            instance.run()
        except Exception, e:
            session.rollback()
            raise e
        else:
            session.commit()
        finally:
            session.close()

    def __init__(self, session, config, task):
        self.session = session
        self.config = config
        self.user_id = task.get('user_id')
        self.repo_id = task.get('repo_id')

    def run(self):
        self.user = self.session.query(User).get(self.user_id)
        if not self.user:
            return
        self.github = Github(self.user.github_access_token)
        if not self.check_permissions():
            return
        repo = self.get_repo()
        if not repo.hook_id:
            self.create_hook(repo)
        else:
            self.delete_hook(repo)

    def check_permissions(self):
        permissions = self.session.query(Permission.id).filter_by(
            user_id=self.user_id, repository_id=self.repo_id, admin=True
        ).count()
        return bool(permissions)

    def get_repo(self):
        return self.session.query(Repository).get(self.repo_id)

    def get_github_repo(self, repo):
        repo_owner = self.github.get_user(repo.owner_name)
        github_repo = repo_owner.get_repo(repo.name)
        return github_repo

    def delete_hook(self, repo):
        github_repo = self.get_github_repo(repo)
        hook = github_repo.get_hook(repo.hook_id)
        hook.delete()
        repo.hook_id = None
        self.session.flush()

    def create_hook(self, repo):
        github_repo = self.get_github_repo(repo)
        listener_url = '{}/?token={}'.format(
            self.config['listener_url'],
            repo.token,
        )
        hook_config = {
            'url': listener_url,
            'content_type': 'json'
        }
        hook = github_repo.create_hook('web', config=hook_config)
        repo.hook_id = hook.id
        self.session.flush()
