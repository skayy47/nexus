"""NEXUS — The Institutional Memory Engine."""

__version__ = "0.1.0"

# langchain-core 0.3.84 bug: accesses langchain.verbose / .debug / .llm_cache
# which were removed in langchain 0.3. Patch them back before any LangChain imports.
try:
    import langchain as _lc

    for _attr, _default in [("verbose", False), ("debug", False), ("llm_cache", None)]:
        if not hasattr(_lc, _attr):
            setattr(_lc, _attr, _default)
except ImportError:
    pass
