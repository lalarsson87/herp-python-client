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

from ..errors.exceptions import (
    HerpAPIError,
    HerpAuthenticationError,
    HerpRateLimitError,
)
from .assignments import AssignmentsAPI
from .async_assignments import AsyncAssignmentsAPI
from .async_base_client import AsyncHerpBaseClient
from .async_batch_client import AsyncBatchHerpClient, AsyncBatchResult
from .async_candidates import AsyncCandidaciesAPI, AsyncHerpPaginator

# Async clients
from .async_client import AsyncHerpClient
from .async_contacts import AsyncContactsAPI
from .async_evaluations import AsyncEvaluationsAPI
from .async_files import AsyncFilesAPI
from .async_master_data import AsyncMasterDataAPI
from .async_timeline import AsyncTimelineAPI
from .base_client import HerpBaseClient
from .batch_client import BatchHerpClient, BatchResult
from .builders import CandidateBuilder  # Alias
from .builders import InterviewBuilder  # Alias
from .builders import (
    CandidacyBuilder,
    ContactBuilder,
    EvaluationResponseBuilder,
)
from .candidates import CandidaciesAPI
from .client import HerpClient
from .contacts import ContactsAPI
from .evaluations import EvaluationsAPI

# Event Sourcing
from .events import (
    AssignmentAdded,
    AssignmentRemoved,
    AuditLogProjection,
    CandidacyCreated,
    CandidacyEvent,
    CandidacyProjection,
    CandidacyStatusChanged,
    CandidacyStepChanged,
    CandidacyTerminated,
    ContactAdded,
    ContactUpdated,
    Event,
    EventSourcedCandidacy,
    EventStore,
    FileUploaded,
    InMemoryEventStore,
    TimelineCommentAdded,
    TimelineProjection,
)
from .files import FilesAPI
from .master_data import MasterDataAPI
from .mixins import (
    BatchFetchMixin,
    CacheMixin,
    MetricsMixin,
    PaginationMixin,
    ValidationMixin,
)

# Query DSL
from .query_dsl import (
    CandidacyQuery,
    FieldFilter,
    FilterOperator,
    LogicalOperator,
    Query,
    candidacy_query,
    query,
)
from .rate_limiter import AdaptiveRateLimiter, AsyncRateLimiter
from .timeline import TimelineAPI

# Webhooks
from .webhooks import (
    AsyncWebhookHandler,
    AsyncWebhookRouter,
    FailedEvent,
    HandlerFunc,
    WebhookEvent,
    WebhookHandler,
    WebhookRoute,
    WebhookRouter,
    WebhookVerificationError,
    WebhookVerifier,
    log_event_handler,
    print_event_handler,
    verify_webhook,
)

# Models - currently not implemented
# from .models import (
#     Candidacy,
#     CandidacyStatus,
#     Contact,
#     ContactType,
#     Evaluation,
#     File,
#     FileType,
#     Requisition,
#     TerminationReason,
#     TimelineComment,
#     User,
# )



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
