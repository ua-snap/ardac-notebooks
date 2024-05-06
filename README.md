# ardac-notebooks

An somewhat misnamed repository for Arctic-EDS "modules" aka "computational notebooks" - functionally these are Jupyter Notebooks than run in a user's browser via JupyterLite.

## Deploy Story

When code is pushed to `main` that triggers a Github workflow that builds and serves the notebook content via a JupyterLite instance hosted at a GitHub pages instance. So, be careful pushing code to main because this will automatically deploy changes to production! Users can access the Github Pages instance directly, but the most common front door will be the Arctic-EDS.

See `.github/workflows` to check out what this deploy Github Action looks like in practice.

I guess the nice thing here is that deploying is super easy, just push to main :rocket:

## Development Story

Development is a lil' tricky because of how JupyterLite and GitHub Pages handle HTTP (vs. HTTPS) requests and because of how JupyterLite can build with an environment distinct from the local development environment.

To get started, I recommend the following steps:

- First, checkout a new branch. Seems obvious, but I'm stating the obvious because `main` is lava here.
- Create / activate the `py310forEDS.yml` conda environment.

```sh
conda env create -f py310forEDD.yml
```

```sh
conda activate py310forEDS
```

Note that we are matching the major version of Python specified in the `.github/workflows/deploy.yml` spec. This conda env is basically our local umbrella environment that lets us touch JupyterLite. The JupyterLite environment / package installation is spec'd by `requirements.txt`.

- Next, build the JupyterLite site like this:

```sh
jupyter lite build --contents content --output-dir dist
```

What this command does is take all the notebooks in the `content` directory and compiles all of it into a bundle of JS/HTML/JSON in a directory called `dist`.

- Now serve that bundle with Python like so:

```sh
cd dist && python -m http.server
```

And navigate to the whichever port that is configured for (probably `8000` but the command should output should tell you where to go): http://localhost:8000/

You should land on a JupyterLab interface that looks pretty much like any other JupyterLab instance you've used. Now you can edit and execute individual notebooks! However, one thing to note about using and developing notebooks within the JupyterLite context is that your browser cache will be sticky. This can be nice (basically autosave for every single user) but also annoying (you expect the notebook to be served in whatever the current branch state is, but you get whatever broken state you last broke it in). Hard refresh your browser, user a private window, or other browser cache dumping strategies as needed.

Test your changes to notebooks using this workflow! This has a few advantages:

- We are testing the JupyterLite build process each time, and not just the local notebook logic.
- GitHub Pages isn't intended for dev / prod splits unless twin repos are used...maintaining one repo feels like enough of a challenge so we want to avoid that.
- When you test your changes you are running the same Web Assembly that the end user will be testing.
- You can do all this without pushing to `main`.
