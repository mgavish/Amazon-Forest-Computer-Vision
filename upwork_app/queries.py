Q_VENDOR_PROPOSALS_PAGED = """
query VendorProposals($filter: VendorProposalFilter!, $sort: VendorProposalSortAttribute!, $pagination: Pagination!) {
  vendorProposals(filter: $filter, sortAttribute: $sort, pagination: $pagination) {
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      cursor
      node {
        id
        proposalCoverLetter
        status { status }
        marketplaceJobPosting { id }
      }
    }
  }
}
"""

Q_VENDOR_PROPOSALS_SNAPSHOT = """
query VendorProposals($filter: VendorProposalFilter!, $sort: VendorProposalSortAttribute!, $pagination: Pagination!) {
  vendorProposals(filter: $filter, sortAttribute: $sort, pagination: $pagination) {
    edges {
      cursor
      node {
        id
        proposalCoverLetter
        status { status }
        marketplaceJobPosting { id }
      }
    }
  }
}
"""

Q_JOB_BY_ID = """
query JobById($id: ID!) {
  marketplaceJobPosting(id: $id) {
    id
    content { title description }
  }
}
"""

Q_JOB_SKILLS = """
query JobSkills($id: ID!) {
  marketplaceJobPosting(id: $id) {
    id
    classification {
      skills { preferredLabel }
      additionalSkills { preferredLabel }
    }
  }
}
"""
