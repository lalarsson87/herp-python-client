#!/usr/bin/env python3
"""
Type definitions for Notion API responses

Uses TypedDict for better type safety and IDE support.
Requires Python 3.8+, uses NotRequired for optional fields (Python 3.11+).
"""

from typing import TypedDict, List, Optional, Literal, Any, Dict

try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired


# ============================================================================
# Common Property Types
# ============================================================================

class RichTextItem(TypedDict, total=False):
    """Notion rich text item"""
    type: Literal['text', 'mention', 'equation']
    text: NotRequired[dict]
    mention: NotRequired[dict]
    equation: NotRequired[dict]
    annotations: NotRequired[dict]
    plain_text: str
    href: NotRequired[str]


class SelectOption(TypedDict):
    """Notion select option"""
    id: NotRequired[str]
    name: str
    color: NotRequired[str]


class User(TypedDict, total=False):
    """Notion user"""
    object: Literal['user']
    id: str
    type: NotRequired[Literal['person', 'bot']]
    name: NotRequired[str]
    avatar_url: NotRequired[str]
    person: NotRequired[dict]
    bot: NotRequired[dict]


class Parent(TypedDict, total=False):
    """Notion parent reference"""
    type: Literal['database_id', 'page_id', 'workspace']
    database_id: NotRequired[str]
    page_id: NotRequired[str]
    workspace: NotRequired[bool]


# ============================================================================
# Property Value Types
# ============================================================================

class TitleProperty(TypedDict):
    """Title property value"""
    type: Literal['title']
    title: List[RichTextItem]


class RichTextProperty(TypedDict):
    """Rich text property value"""
    type: Literal['rich_text']
    rich_text: List[RichTextItem]


class NumberProperty(TypedDict):
    """Number property value"""
    type: Literal['number']
    number: Optional[float]


class SelectProperty(TypedDict):
    """Select property value"""
    type: Literal['select']
    select: Optional[SelectOption]


class MultiSelectProperty(TypedDict):
    """Multi-select property value"""
    type: Literal['multi_select']
    multi_select: List[SelectOption]


class DateProperty(TypedDict, total=False):
    """Date property value"""
    type: Literal['date']
    date: NotRequired[dict]  # Contains start, end, time_zone


class PeopleProperty(TypedDict):
    """People property value"""
    type: Literal['people']
    people: List[User]


class FilesProperty(TypedDict):
    """Files property value"""
    type: Literal['files']
    files: List[dict]


class CheckboxProperty(TypedDict):
    """Checkbox property value"""
    type: Literal['checkbox']
    checkbox: bool


class URLProperty(TypedDict):
    """URL property value"""
    type: Literal['url']
    url: Optional[str]


class EmailProperty(TypedDict):
    """Email property value"""
    type: Literal['email']
    email: Optional[str]


class PhoneNumberProperty(TypedDict):
    """Phone number property value"""
    type: Literal['phone_number']
    phone_number: Optional[str]


class RelationProperty(TypedDict):
    """Relation property value"""
    type: Literal['relation']
    relation: List[dict]  # List of page references


class CreatedTimeProperty(TypedDict):
    """Created time property value"""
    type: Literal['created_time']
    created_time: str


class LastEditedTimeProperty(TypedDict):
    """Last edited time property value"""
    type: Literal['last_edited_time']
    last_edited_time: str


# Union of all property types
PropertyValue = (
    TitleProperty |
    RichTextProperty |
    NumberProperty |
    SelectProperty |
    MultiSelectProperty |
    DateProperty |
    PeopleProperty |
    FilesProperty |
    CheckboxProperty |
    URLProperty |
    EmailProperty |
    PhoneNumberProperty |
    RelationProperty |
    CreatedTimeProperty |
    LastEditedTimeProperty
)


# ============================================================================
# Page Types
# ============================================================================

class PageResponse(TypedDict, total=False):
    """Notion page response"""
    object: Literal['page']
    id: str
    created_time: str
    last_edited_time: str
    created_by: User
    last_edited_by: User
    cover: NotRequired[dict]
    icon: NotRequired[dict]
    parent: Parent
    archived: bool
    properties: Dict[str, PropertyValue]
    url: str


class PageCreateRequest(TypedDict, total=False):
    """Request for creating a page"""
    parent: Parent
    properties: Dict[str, PropertyValue]
    children: NotRequired[List[dict]]  # Block children
    icon: NotRequired[dict]
    cover: NotRequired[dict]


class PageUpdateRequest(TypedDict, total=False):
    """Request for updating a page"""
    properties: NotRequired[Dict[str, PropertyValue]]
    archived: NotRequired[bool]
    icon: NotRequired[dict]
    cover: NotRequired[dict]


# ============================================================================
# Database Types
# ============================================================================

class DatabasePropertyConfig(TypedDict, total=False):
    """Database property configuration"""
    id: NotRequired[str]
    name: NotRequired[str]
    type: str
    # Type-specific configs
    number: NotRequired[dict]
    select: NotRequired[dict]
    multi_select: NotRequired[dict]
    date: NotRequired[dict]
    people: NotRequired[dict]
    files: NotRequired[dict]
    checkbox: NotRequired[dict]
    url: NotRequired[dict]
    email: NotRequired[dict]
    phone_number: NotRequired[dict]
    formula: NotRequired[dict]
    relation: NotRequired[dict]
    rollup: NotRequired[dict]
    created_time: NotRequired[dict]
    created_by: NotRequired[dict]
    last_edited_time: NotRequired[dict]
    last_edited_by: NotRequired[dict]


class DatabaseResponse(TypedDict, total=False):
    """Notion database response"""
    object: Literal['database']
    id: str
    created_time: str
    last_edited_time: str
    created_by: User
    last_edited_by: User
    title: List[RichTextItem]
    description: NotRequired[List[RichTextItem]]
    icon: NotRequired[dict]
    cover: NotRequired[dict]
    properties: Dict[str, DatabasePropertyConfig]
    parent: Parent
    url: str
    archived: bool
    is_inline: NotRequired[bool]


class DatabaseQueryRequest(TypedDict, total=False):
    """Request for querying a database"""
    filter: NotRequired[dict]
    sorts: NotRequired[List[dict]]
    start_cursor: NotRequired[str]
    page_size: NotRequired[int]


class DatabaseQueryResponse(TypedDict):
    """Response for database query"""
    object: Literal['list']
    results: List[PageResponse]
    next_cursor: Optional[str]
    has_more: bool
    type: Literal['page']
    page: NotRequired[dict]


# ============================================================================
# Block Types
# ============================================================================

class BlockResponse(TypedDict, total=False):
    """Notion block response"""
    object: Literal['block']
    id: str
    parent: Parent
    type: str
    created_time: str
    created_by: User
    last_edited_time: str
    last_edited_by: User
    archived: bool
    has_children: bool
    # Type-specific content (paragraph, heading_1, etc.)


class BlockChildrenResponse(TypedDict):
    """Response for list block children"""
    object: Literal['list']
    results: List[BlockResponse]
    next_cursor: Optional[str]
    has_more: bool
    type: Literal['block']


# ============================================================================
# Search Types
# ============================================================================

class SearchRequest(TypedDict, total=False):
    """Request for searching Notion"""
    query: NotRequired[str]
    filter: NotRequired[dict]
    sort: NotRequired[dict]
    start_cursor: NotRequired[str]
    page_size: NotRequired[int]


class SearchResponse(TypedDict):
    """Response for search"""
    object: Literal['list']
    results: List[PageResponse | DatabaseResponse]
    next_cursor: Optional[str]
    has_more: bool


# ============================================================================
# Error Response Types
# ============================================================================

class NotionErrorResponse(TypedDict, total=False):
    """Notion API error response"""
    object: Literal['error']
    status: int
    code: str
    message: str


# ============================================================================
# Helper Types for HERP-Notion Integration
# ============================================================================

class CandidatePageProperties(TypedDict, total=False):
    """Properties for candidate pages in Notion"""
    Name: TitleProperty
    Email: EmailProperty
    Phone: PhoneNumberProperty
    Status: SelectProperty
    Step: SelectProperty
    Requisition: RelationProperty
    Tags: MultiSelectProperty
    Created: CreatedTimeProperty
    Updated: LastEditedTimeProperty
    HERP_ID: RichTextProperty
    Resume_URL: URLProperty


class InterviewPageProperties(TypedDict, total=False):
    """Properties for interview pages in Notion"""
    Title: TitleProperty
    Candidate: RelationProperty
    Type: SelectProperty
    Date: DateProperty
    Interviewers: PeopleProperty
    Notes: RichTextProperty
    HERP_Contact_ID: RichTextProperty


class EvaluationPageProperties(TypedDict, total=False):
    """Properties for evaluation pages in Notion"""
    Candidate: RelationProperty
    Interview: RelationProperty
    Evaluator: PeopleProperty
    Score: NumberProperty
    Recommendation: SelectProperty
    Notes: RichTextProperty
    HERP_Evaluation_ID: RichTextProperty
