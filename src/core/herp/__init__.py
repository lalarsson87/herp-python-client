"""
HERP API Client and Utilities

The HERP client provides a modular architecture for interacting with the HERP Hire API:

Main Clients:
    - HerpClient: Synchronous facade client with backward-compatible methods
    - AsyncHerpClient: Asynchronous client for non-blocking operations

Specialized API Clients (Sync):
    - CandidaciesAPI: Candidacy operations
    - ContactsAPI: Interview/contact operations
    - FilesAPI: File operations
    - EvaluationsAPI: Evaluation operations
    - AssignmentsAPI: Team assignment operations
    - TimelineAPI: Timeline comment operations
    - MasterDataAPI: Requisitions and users

Specialized API Clients (Async):
    - AsyncCandidaciesAPI: Async candidacy operations
    - AsyncContactsAPI: Async interview/contact operations
    - AsyncFilesAPI: Async file operations
    - AsyncEvaluationsAPI: Async evaluation operations
    - AsyncAssignmentsAPI: Async team assignment operations
    - AsyncTimelineAPI: Async timeline comment operations
    - AsyncMasterDataAPI: Async requisitions and users

Supporting Components:
    - HerpBaseClient: Synchronous HTTP client with auth and rate limiting
    - AsyncHerpBaseClient: Asynchronous HTTP client
    - BatchHerpClient: Synchronous bulk operations client
    - AsyncBatchHerpClient: Asynchronous bulk operations client
    - AdaptiveRateLimiter: Smart rate limiting (sync)
    - AsyncRateLimiter: Smart rate limiting (async)

Exceptions:
    - HerpAPIError: General API errors
    - HerpRateLimitError: Rate limit errors
    - HerpAuthenticationError: Authentication errors
"""

from .client import HerpClient
from .base_client import HerpBaseClient
from .batch_client import BatchHerpClient, BatchResult
from .rate_limiter import HerpRateLimiter, AdaptiveRateLimiter, AsyncRateLimiter
from .candidates import CandidaciesAPI
from .contacts import ContactsAPI
from .files import FilesAPI
from .evaluations import EvaluationsAPI
from .assignments import AssignmentsAPI
from .timeline import TimelineAPI
from .master_data import MasterDataAPI

# Async clients
from .async_client import AsyncHerpClient
from .async_base_client import AsyncHerpBaseClient
from .async_batch_client import AsyncBatchHerpClient, AsyncBatchResult
from .async_candidates import AsyncCandidaciesAPI, AsyncHerpPaginator, SearchQuery
from .async_contacts import AsyncContactsAPI
from .async_files import AsyncFilesAPI
from .async_evaluations import AsyncEvaluationsAPI
from .async_assignments import AsyncAssignmentsAPI
from .async_timeline import AsyncTimelineAPI
from .async_master_data import AsyncMasterDataAPI

# Query DSL
from .query_dsl import (
    Query,
    CandidacyQuery,
    FieldFilter,
    FilterOperator,
    LogicalOperator,
    query,
    candidacy_query,
)

# Event Sourcing
from .events import (
    Event,
    CandidacyEvent,
    CandidacyCreated,
    CandidacyStepChanged,
    CandidacyStatusChanged,
    CandidacyTerminated,
    ContactAdded,
    ContactUpdated,
    FileUploaded,
    TimelineCommentAdded,
    AssignmentAdded,
    AssignmentRemoved,
    EventStore,
    InMemoryEventStore,
    EventSourcedCandidacy,
    CandidacyProjection,
    TimelineProjection,
    AuditLogProjection,
    AnalyticsProjection,
)

# Webhooks
from .webhooks import (
    WebhookVerifier,
    WebhookVerificationError,
    verify_webhook,
    WebhookEvent,
    WebhookHandler,
    AsyncWebhookHandler,
    HandlerFunc,
    log_event_handler,
    print_event_handler,
    WebhookRoute,
    WebhookRouter,
    AsyncWebhookRouter,
    FailedEvent,
)

from .builders import (
    CandidacyBuilder,
    ContactBuilder,
    EvaluationResponseBuilder,
    CandidateBuilder,  # Alias
    InterviewBuilder,  # Alias
)
from .mixins import (
    BatchFetchMixin,
    PaginationMixin,
    ValidationMixin,
    MetricsMixin,
    CacheMixin,
)
from ..errors.exceptions import (
    HerpAPIError,
    HerpRateLimitError,
    HerpAuthenticationError,
)
from .models import (
    Candidacy,
    Contact,
    Evaluation,
    TimelineComment,
    File,
    Requisition,
    User,
    CandidacyStatus,
    TerminationReason,
    ContactType,
    FileType
)

__all__ = [
    # Main Clients (Sync)
    "HerpClient",
    "HerpBaseClient",
    "BatchHerpClient",
    "BatchResult",

    # Main Clients (Async)
    "AsyncHerpClient",
    "AsyncHerpBaseClient",
    "AsyncBatchHerpClient",
    "AsyncBatchResult",

    # Specialized API Clients (Sync)
    "CandidaciesAPI",
    "ContactsAPI",
    "FilesAPI",
    "EvaluationsAPI",
    "AssignmentsAPI",
    "TimelineAPI",
    "MasterDataAPI",

    # Specialized API Clients (Async)
    "AsyncCandidaciesAPI",
    "AsyncContactsAPI",
    "AsyncFilesAPI",
    "AsyncEvaluationsAPI",
    "AsyncAssignmentsAPI",
    "AsyncTimelineAPI",
    "AsyncMasterDataAPI",

    # Helpers
    "AsyncHerpPaginator",
    "SearchQuery",

    # Query DSL
    "Query",
    "CandidacyQuery",
    "FieldFilter",
    "FilterOperator",
    "LogicalOperator",
    "query",
    "candidacy_query",

    # Event Sourcing
    "Event",
    "CandidacyEvent",
    "CandidacyCreated",
    "CandidacyStepChanged",
    "CandidacyStatusChanged",
    "CandidacyTerminated",
    "ContactAdded",
    "ContactUpdated",
    "FileUploaded",
    "TimelineCommentAdded",
    "AssignmentAdded",
    "AssignmentRemoved",
    "EventStore",
    "InMemoryEventStore",
    "EventSourcedCandidacy",
    "CandidacyProjection",
    "TimelineProjection",
    "AuditLogProjection",
    "AnalyticsProjection",

    # Webhooks
    "WebhookVerifier",
    "WebhookVerificationError",
    "verify_webhook",
    "WebhookEvent",
    "WebhookHandler",
    "AsyncWebhookHandler",
    "HandlerFunc",
    "log_event_handler",
    "print_event_handler",
    "WebhookRoute",
    "WebhookRouter",
    "AsyncWebhookRouter",
    "FailedEvent",

    # Builders
    "CandidacyBuilder",
    "ContactBuilder",
    "EvaluationResponseBuilder",
    "CandidateBuilder",  # Alias
    "InterviewBuilder",  # Alias

    # Mixins
    "BatchFetchMixin",
    "PaginationMixin",
    "ValidationMixin",
    "MetricsMixin",
    "CacheMixin",

    # Exceptions
    "HerpAPIError",
    "HerpRateLimitError",
    "HerpAuthenticationError",

    # Rate Limiters
    "HerpRateLimiter",
    "AdaptiveRateLimiter",
    "AsyncRateLimiter",

    # Models
    "Candidacy",
    "Contact",
    "Evaluation",
    "TimelineComment",
    "File",
    "Requisition",
    "User",

    # Enums
    "CandidacyStatus",
    "TerminationReason",
    "ContactType",
    "FileType",
]
