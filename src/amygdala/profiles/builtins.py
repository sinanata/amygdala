"""Built-in extension profiles."""

from __future__ import annotations

from amygdala.profiles.models import ExtensionProfile

UNITY = ExtensionProfile(
    name="unity",
    description="Unity game engine (C#, ShaderLab, YAML scenes)",
    extensions=frozenset({
        ".shader", ".hlsl", ".cginc", ".compute",
        ".unity", ".prefab", ".asset", ".mat", ".meta",
        ".asmdef", ".asmref", ".controller", ".anim",
        ".shadergraph", ".uxml", ".uss",
    }),
    language_map={
        ".shader": "shaderlab",
        ".unity": "yaml",
        ".prefab": "yaml",
        ".asset": "yaml",
        ".mat": "yaml",
        ".meta": "yaml",
        ".hlsl": "hlsl",
        ".cginc": "hlsl",
        ".compute": "hlsl",
        ".asmdef": "json",
        ".asmref": "json",
        ".uxml": "xml",
        ".uss": "css",
    },
    exclude_patterns=["Library/", "Temp/", "Obj/", "UserSettings/", "Logs/"],
)

UNREAL = ExtensionProfile(
    name="unreal",
    description="Unreal Engine (C++, HLSL, .uproject)",
    extensions=frozenset({
        ".inl", ".uproject", ".uplugin",
        ".usf", ".ush", ".uasset", ".umap",
    }),
    language_map={
        ".uproject": "json",
        ".uplugin": "json",
        ".usf": "hlsl",
        ".ush": "hlsl",
        ".inl": "cpp",
    },
    exclude_patterns=["Binaries/", "DerivedDataCache/", "Intermediate/", "Saved/"],
)

PYTHON = ExtensionProfile(
    name="python",
    description="Python ecosystem (stubs, Cython, Jupyter)",
    extensions=frozenset({
        ".pyi", ".pyx", ".pxd", ".ipynb", ".in", ".conf",
    }),
    language_map={
        ".pyi": "python",
        ".pyx": "cython",
        ".pxd": "cython",
        ".ipynb": "jupyter",
    },
    exclude_patterns=[
        "__pycache__/", ".venv/", ".tox/",
        ".mypy_cache/", ".pytest_cache/", ".ruff_cache/",
    ],
)

NODE = ExtensionProfile(
    name="node",
    description="Node.js ecosystem (ESM/CJS, TypeScript variants)",
    extensions=frozenset({
        ".mjs", ".cjs", ".mts", ".cts", ".npmrc",
    }),
    language_map={
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".mts": "typescript",
        ".cts": "typescript",
        ".npmrc": "ini",
    },
    exclude_patterns=["node_modules/", ".next/", ".nuxt/", ".cache/", ".turbo/"],
)

REACT = ExtensionProfile(
    name="react",
    description="React ecosystem (SCSS, Sass, Less, SVG, MDX)",
    extensions=frozenset({
        ".scss", ".sass", ".less", ".svg", ".mdx",
    }),
    language_map={
        ".scss": "scss",
        ".sass": "sass",
        ".less": "less",
        ".svg": "xml",
        ".mdx": "mdx",
    },
    exclude_patterns=["node_modules/", "storybook-static/", "coverage/"],
)

NEXTJS = ExtensionProfile(
    name="nextjs",
    description="Next.js framework (MDX, SCSS, SVG)",
    extensions=frozenset({
        ".mdx", ".scss", ".svg",
    }),
    language_map={
        ".mdx": "mdx",
        ".scss": "scss",
        ".svg": "xml",
    },
    exclude_patterns=[".next/", ".vercel/", "out/", "node_modules/"],
)

BUILTIN_PROFILES: dict[str, ExtensionProfile] = {
    p.name: p for p in [UNITY, UNREAL, PYTHON, NODE, REACT, NEXTJS]
}
