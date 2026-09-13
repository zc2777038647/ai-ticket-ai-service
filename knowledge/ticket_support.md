# Ticket support knowledge

## Account and login

For account or login failures, verify the username, password reset path, and whether the account is active. Never ask a user to disclose a password or access token in a ticket.

## Priority guidance

Use URGENT only when a production-wide outage, data-loss risk, or security incident blocks normal service. Use HIGH for a severe user-impacting failure with a workaround unavailable. MEDIUM is appropriate for a normal business-impacting issue; LOW is for questions and cosmetic problems.

## Reply guidance

客服回复应确认已收到问题、复述当前理解、说明下一步和预计跟进方式。回复草稿必须经过人工审核后才能发送，不得自动代表客服做承诺。

## Security guidance

Never expose another user's ticket. Java owns authentication, authorization, and ticket updates; the AI service only receives the minimum data needed to produce advice.
