import requests
from datetime import datetime
from rich.syntax import Syntax
from dataclasses import dataclass
from huggingface_hub import HfApi
from rich.traceback import Traceback
from textual.widgets import Tree, Rule
from textual.containers import Horizontal
from huggingface_hub import hf_hub_download
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container, VerticalScroll

class ModelAuthor:
    def __init__(self, author_data):
        self.avatar_url = author_data.get('avatarUrl')
        self.fullname = author_data.get('fullname')
        self.name = author_data.get('name')
        self.type = author_data.get('type')
        self.is_hf = author_data.get('isHf', False)
        self.is_enterprise = author_data.get('isEnterprise', False)
        self.is_pro = author_data.get('isPro', False)

class Model:
    def __init__(self, model_data):
        self.author = model_data.get('author')
        self.author_data = ModelAuthor(model_data.get('authorData', {}))
        self.downloads = model_data.get('downloads')
        self.gated = model_data.get('gated')
        self.model_id = model_data.get('id')
        self.last_modified = datetime.fromisoformat(model_data.get('lastModified'))
        self.likes = model_data.get('likes')
        self.pipeline_tag = model_data.get('pipeline_tag')
        self.private = model_data.get('private')
        self.repo_type = model_data.get('repoType')
        self.is_liked_by_user = model_data.get('isLikedByUser', False)

class ModelsResponse:
    def __init__(self, response_data):
        self.active_filters = response_data.get('activeFilters')
        self.models = [Model(model) for model in response_data.get('models', [])]
        self.num_items_per_page = response_data.get('numItemsPerPage')
        self.num_total_items = response_data.get('numTotalItems')
        self.page_index = response_data.get('pageIndex')


class HuggingFaceModelFetcher:
    def __init__(self, base_url='https://huggingface.co/models-json'):
        self.base_url = base_url
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-GB,en;q=0.8',
            'referer': 'https://huggingface.co/models?p=1&sort=trending',
            'sec-ch-ua': '"Brave";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }

    def fetch_models(self, page=1, sort='trending'):
        params = {'p': page, 'sort': sort}
        response = requests.get(self.base_url, headers=self.headers, params=params)
        if response.status_code == 200:
            return ModelsResponse(response.json())
        else:
            raise Exception(f"Failed to fetch data: {response.status_code}")
        
@dataclass
class RepoEntry:
    repo: str
    path: str
    loaded: bool = False


class FileView(Tree):  
    CSS_PATH = "hugginface.tcss"

    def compose(self) -> ComposeResult:
        # with Horizontal():
        yield Horizontal(
            Tree("Repo", id="model_files"),
            Rule(orientation="vertical"),
            VerticalScroll(Static(id="code", expand=True))
        )

    def on_tree_node_selected(
        self, event: Tree.NodeSelected
    ) -> None:
        """Called when the user click a file in the directory tree."""
        
        code_view = self.query_one("#code", Static)
        code_view.title = event.node.label
        syntax = ""
        
        try:
            data = event.node.data
            # check extension: we only want .md, .json, .py files
            if not data.path.endswith((".md", ".json", ".py")):
                event.stop()
                return
            
            try:
                file = hf_hub_download(str(data.repo), str(data.path))
                
                syntax = Syntax.from_path(
                    file,
                    line_numbers=True,
                    word_wrap=False,
                    indent_guides=True,
                    theme="github-dark",
                )
            except Exception as e:
                code_view.update(Traceback(theme="github-dark", width=None))
                self.sub_title = "ERROR"

        except Exception:
            pass
        else:
            code_view.update(syntax)
            self.sub_title = str(event.node.label)

        self.refresh()
        event.stop()


class HuggingFace(App):
    TITLE = "Hugging Face 🤗"
    
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit"),
        ("?", "show_help", "Show help"),
        ("m", "fetch_models", "More models"),
        ("f", "toggle_models", "Toggle Models"),
        ]

    CSS_PATH = "hugginface.tcss"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dark = True
        self.limit = 30
        self.page = 1
        self.total_models = 0
        self.models = []
        self.sort = 'trending' # available options: trending, created, modified, likes, downloads
        self.modelsRoot = None
        self.models_tree = None  # Initialize the tree reference
        self.fetcher = HuggingFaceModelFetcher()

    def on_mount(self) -> None:
        """Load initial models on app start."""
        self.fetch_models()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        self.models_tree = Tree("Hugging Face 🤗", id="models_tree")
        self.models_tree.root.expand()
        with Container():
            yield self.models_tree
            yield Rule()
            yield FileView(label="Files", id="file_view")

        yield Footer()
   
    def update_tree_view(self):
        """Update the tree view with models."""
        models_tree = self.models_tree 
        self.models_tree.root.expand()
        self.modelsRoot = self.models_tree.root.add(f"Models Page {self.page}", data=self.models, expand=True)
        if models_tree:
            for model in self.models:
                self.modelsRoot.add_leaf(model.model_id, data=model)
        
    def action_fetch_models(self):
        self.page += 1
        self.fetch_models(page=self.page)
        self.refresh()

    def fetch_models(self, page=1):
        """Fetch models from HuggingFace and update the tree."""
        response = self.fetcher.fetch_models(page=page, sort=self.sort)
        self.models = response.models
        self.total_models = response.num_total_items
        self.update_tree_view()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark
        self.refresh()

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """When a node is highlighted, show the model details."""
        event.stop()
        code_view = self.query_one("#model_files", Tree)
        code_view.title = event.node.label
        model = event.node.label
        code_view.root.expand()

        try:
            api = HfApi()
            files = api.list_repo_files(str(model))
            code_view.clear()

            modelsRoot = code_view.root.add(model, data=files, expand=True)

            if modelsRoot:
                for file in files:
                    modelsRoot.add_leaf(file, RepoEntry(repo=model, path=file))

            code_view.refresh()
        
        except Exception as e:
            pass

    def action_toggle_models(self):
        tree = self.query_one(Tree)
        tree.show_root = not tree.show_root

if __name__ == "__main__":
    HuggingFace().run()
