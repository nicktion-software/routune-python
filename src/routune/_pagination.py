from __future__ import annotations

from typing import Any, AsyncIterator, Awaitable, Callable, Generator, Generic, Iterator, TypeVar

import pydantic

T = TypeVar("T", bound=pydantic.BaseModel)

__all__ = ["SyncPage", "AsyncPage", "AsyncPaginator"]


def _items(model: type[T], body: dict[str, Any]) -> list[T]:
    return [model.model_validate(item) for item in body.get("data") or []]


class SyncPage(Generic[T]):
    """One page of a list (newest first). Iterate it to walk every item across all pages."""

    def __init__(self, model: type[T], body: dict[str, Any], fetch: Callable[[str], dict[str, Any]]) -> None:
        self._model = model
        self._fetch = fetch
        self.object = "list"
        self.data: list[T] = _items(model, body)
        self.has_more: bool = bool(body.get("has_more"))
        self.next_cursor: str | None = body.get("next_cursor")

    def has_next_page(self) -> bool:
        return self.has_more and bool(self.next_cursor)

    def get_next_page(self) -> SyncPage[T]:
        if not self.has_next_page():
            raise RuntimeError("No next page. Check has_next_page() first.")
        return SyncPage(self._model, self._fetch(self.next_cursor or ""), self._fetch)

    def iter_pages(self) -> Iterator[SyncPage[T]]:
        page: SyncPage[T] = self
        yield page
        while page.has_next_page():
            page = page.get_next_page()
            yield page

    def __iter__(self) -> Iterator[T]:
        for page in self.iter_pages():
            yield from page.data

    def __repr__(self) -> str:
        return f"SyncPage(data=[{len(self.data)} items], has_more={self.has_more}, next_cursor={self.next_cursor!r})"


class AsyncPage(Generic[T]):
    """One page of a list. ``async for`` over it walks every item across all pages."""

    def __init__(
        self, model: type[T], body: dict[str, Any], fetch: Callable[[str], Awaitable[dict[str, Any]]]
    ) -> None:
        self._model = model
        self._fetch = fetch
        self.object = "list"
        self.data: list[T] = _items(model, body)
        self.has_more: bool = bool(body.get("has_more"))
        self.next_cursor: str | None = body.get("next_cursor")

    def has_next_page(self) -> bool:
        return self.has_more and bool(self.next_cursor)

    async def get_next_page(self) -> AsyncPage[T]:
        if not self.has_next_page():
            raise RuntimeError("No next page. Check has_next_page() first.")
        return AsyncPage(self._model, await self._fetch(self.next_cursor or ""), self._fetch)

    async def iter_pages(self) -> AsyncIterator[AsyncPage[T]]:
        page: AsyncPage[T] = self
        yield page
        while page.has_next_page():
            page = await page.get_next_page()
            yield page

    async def __aiter__(self) -> AsyncIterator[T]:
        async for page in self.iter_pages():
            for item in page.data:
                yield item

    def __repr__(self) -> str:
        return f"AsyncPage(data=[{len(self.data)} items], has_more={self.has_more}, next_cursor={self.next_cursor!r})"


class AsyncPaginator(Generic[T]):
    """What async list methods return: ``await`` it for the first page, ``async for`` for every item."""

    def __init__(
        self, model: type[T], fetch: Callable[[str | None], Awaitable[dict[str, Any]]], first_cursor: str | None
    ) -> None:
        self._model = model
        self._fetch = fetch
        self._first_cursor = first_cursor

    async def _first(self) -> AsyncPage[T]:
        return AsyncPage(self._model, await self._fetch(self._first_cursor), self._fetch)

    def __await__(self) -> Generator[Any, None, AsyncPage[T]]:
        return self._first().__await__()

    async def __aiter__(self) -> AsyncIterator[T]:
        page = await self._first()
        async for item in page:
            yield item
