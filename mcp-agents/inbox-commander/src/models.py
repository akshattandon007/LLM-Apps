"""Pydantic models for Inbox Commander request/response payloads."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class Message(BaseModel):
    id: str
    thread_id: str
    sender: str = ""
    recipient: str = ""
    subject: str = ""
    date: str = ""
    snippet: str = ""
    body: str = ""


class ThreadSummary(BaseModel):
    thread_id: str
    subject: str = ""
    sender: str = ""
    date: str = ""
    snippet: str = ""
    message_count: int = 0


class Thread(BaseModel):
    thread_id: str
    subject: str = ""
    messages: List[Message] = Field(default_factory=list)


class Draft(BaseModel):
    thread_id: str
    tone: str = "professional"
    body: str = ""


class Approval(BaseModel):
    status: str = "approved"
    thread_id: str
    approval_token: str
    note: str = "Pass approval_token to send_draft to send."


class SendResult(BaseModel):
    status: str = "sent"
    message_id: str
    thread_id: str


class LabelResult(BaseModel):
    status: str = "labeled"
    thread_id: str
    label: str


class ArchiveResult(BaseModel):
    status: str = "archived"
    thread_id: str
