import github

def create_gist():
    gh = github.Github("auth token")
    gh_auth_user = gh.get_user()
    gist = gh_auth_user.create_gist( <parameters> )
