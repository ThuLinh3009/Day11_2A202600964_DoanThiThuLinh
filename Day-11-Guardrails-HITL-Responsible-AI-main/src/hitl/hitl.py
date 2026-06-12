"""
Lab 11 — Part 4: Human-in-the-Loop Design
  TODO 12: Confidence Router
  TODO 13: Design 3 HITL decision points
"""
from dataclasses import dataclass


# ============================================================
# TODO 12: Implement ConfidenceRouter
#
# Định tuyến dựa trên confidence score VÀ loại hành động.
# Nguyên tắc: high-risk action luôn cần human dù confidence cao.
# ============================================================

HIGH_RISK_ACTIONS = [
    "transfer_money",
    "close_account",
    "change_password",
    "delete_data",
    "update_personal_info",
]


@dataclass
class RoutingDecision:
    """Result of the confidence router."""
    action: str          # "auto_send", "queue_review", "escalate"
    confidence: float
    reason: str
    priority: str        # "low", "normal", "high"
    requires_human: bool


class ConfidenceRouter:
    """Route agent responses based on confidence and risk level.

    Thresholds:
        HIGH:   confidence >= 0.9 -> auto-send
        MEDIUM: 0.7 <= confidence < 0.9 -> queue for review
        LOW:    confidence < 0.7 -> escalate to human

    High-risk actions always escalate regardless of confidence.
    Lý do: trong banking, một giao dịch sai không thể hoàn tác —
    chi phí của false negative (bỏ lọt) cao hơn false positive.
    """

    HIGH_THRESHOLD = 0.9
    MEDIUM_THRESHOLD = 0.7

    def route(self, response: str, confidence: float,
              action_type: str = "general") -> RoutingDecision:
        """Route a response based on confidence score and action type.

        Args:
            response: The agent's response text
            confidence: Confidence score between 0.0 and 1.0
            action_type: Type of action (e.g., "general", "transfer_money")

        Returns:
            RoutingDecision with routing action and metadata
        """
        # High-risk action: luôn escalate bất kể confidence
        if action_type in HIGH_RISK_ACTIONS:
            return RoutingDecision(
                action="escalate",
                confidence=confidence,
                reason=f"High-risk action: {action_type}",
                priority="high",
                requires_human=True,
            )

        # Confidence cao — tự động gửi
        if confidence >= self.HIGH_THRESHOLD:
            return RoutingDecision(
                action="auto_send",
                confidence=confidence,
                reason="High confidence",
                priority="low",
                requires_human=False,
            )

        # Confidence trung bình — xếp hàng chờ review
        if confidence >= self.MEDIUM_THRESHOLD:
            return RoutingDecision(
                action="queue_review",
                confidence=confidence,
                reason="Medium confidence — needs review",
                priority="normal",
                requires_human=True,
            )

        # Confidence thấp — escalate ngay
        return RoutingDecision(
            action="escalate",
            confidence=confidence,
            reason="Low confidence — escalating",
            priority="high",
            requires_human=True,
        )


# ============================================================
# TODO 13: Design 3 HITL decision points
#
# Ba tình huống thực tế trong banking cần human judgment.
# Mỗi điểm dùng một HITL model khác nhau:
# - human-in-the-loop: human quyết định TRƯỚC khi action xảy ra
# - human-on-the-loop: AI action xảy ra, human có thể override
# - human-as-tiebreaker: hai nguồn mâu thuẫn, human quyết định
# ============================================================

hitl_decision_points = [
    {
        "id": 1,
        "name": "Large Transaction Approval",
        # Giao dịch lớn cần human xác nhận TRƯỚC khi thực hiện
        "trigger": (
            "Giao dịch chuyển tiền > 50 triệu VND, hoặc bất kỳ giao dịch nào "
            "đến tài khoản nước ngoài, hoặc confidence score < 0.85 trên "
            "intent 'transfer_money'."
        ),
        "hitl_model": "human-in-the-loop",
        "context_needed": (
            "Tên người dùng + lịch sử giao dịch 30 ngày, "
            "số tiền + tài khoản đích + thời điểm giao dịch, "
            "alert nếu lần đầu chuyển đến tài khoản này, "
            "địa chỉ IP + thiết bị đăng nhập."
        ),
        "example": (
            "Khách hàng Nguyễn Văn A yêu cầu chuyển 200 triệu VND đến "
            "tài khoản MB Bank lúc 2 giờ sáng — lần đầu chuyển đến TK này. "
            "Hệ thống tạm giữ, gửi OTP + thông báo SMS để xác nhận. "
            "Banker trực ca đêm review trong 5 phút trước khi approve."
        ),
    },
    {
        "id": 2,
        "name": "Compliance & AML Flagging",
        # AI phát hiện pattern đáng ngờ, nhưng human quyết định có report không
        "trigger": (
            "Agent phát hiện pattern đáng ngờ: nhiều giao dịch nhỏ liên tiếp "
            "(structuring), giao dịch bất thường so với lịch sử, "
            "hoặc keyword liên quan đến rủi ro AML trong chat."
        ),
        "hitl_model": "human-on-the-loop",
        "context_needed": (
            "Lịch sử giao dịch 90 ngày, profile khách hàng (nghề nghiệp, "
            "thu nhập khai báo), danh sách đen + watchlist, "
            "transcript cuộc trò chuyện với agent, risk score tự động."
        ),
        "example": (
            "Trong 1 tuần, khách hàng thực hiện 15 giao dịch nạp tiền "
            "mỗi lần 9.9 triệu VND (dưới ngưỡng báo cáo 10 triệu). "
            "AI tự động ghi log + gắn cờ 'potential structuring'. "
            "Compliance officer nhận alert, có 24h để quyết định "
            "có file SAR (Suspicious Activity Report) hay không."
        ),
    },
    {
        "id": 3,
        "name": "Customer Dispute Resolution",
        # Hai bên (AI + khách hàng) không đồng ý, human làm trọng tài
        "trigger": (
            "Khách hàng khiếu nại kết quả AI trả lời (tranh chấp giao dịch, "
            "phàn nàn về lãi suất tính sai), hoặc agent confidence < 0.7 "
            "khi trả lời câu hỏi liên quan đến quyền lợi tài chính."
        ),
        "hitl_model": "human-as-tiebreaker",
        "context_needed": (
            "Transcript đầy đủ cuộc trò chuyện, hợp đồng/điều khoản liên quan, "
            "lịch sử giao dịch bị tranh chấp, policy hiện hành của ngân hàng, "
            "precedent cases tương tự đã giải quyết."
        ),
        "example": (
            "Khách hàng cho rằng lãi suất thẻ tín dụng bị tính sai trong tháng 5. "
            "AI tính theo policy mới (áp dụng từ 01/05), khách hàng dẫn policy cũ. "
            "Hai bên không thống nhất. Case được escalate lên chuyên viên CSKH, "
            "người này có quyền override quyết định của AI và điều chỉnh "
            "nếu xác nhận lỗi hệ thống."
        ),
    },
]


# ============================================================
# Quick tests
# ============================================================

def test_confidence_router():
    """Test ConfidenceRouter with sample scenarios."""
    router = ConfidenceRouter()

    test_cases = [
        ("Balance inquiry", 0.95, "general"),
        ("Interest rate question", 0.82, "general"),
        ("Ambiguous request", 0.55, "general"),
        ("Transfer $50,000", 0.98, "transfer_money"),
        ("Close my account", 0.91, "close_account"),
    ]

    print("Testing ConfidenceRouter:")
    print("=" * 80)
    print(f"{'Scenario':<25} {'Conf':<6} {'Action Type':<18} {'Decision':<15} {'Priority':<10} {'Human?'}")
    print("-" * 80)

    for scenario, conf, action_type in test_cases:
        decision = router.route(scenario, conf, action_type)
        print(
            f"{scenario:<25} {conf:<6.2f} {action_type:<18} "
            f"{decision.action:<15} {decision.priority:<10} "
            f"{'Yes' if decision.requires_human else 'No'}"
        )

    print("=" * 80)


def test_hitl_points():
    """Display HITL decision points."""
    print("\nHITL Decision Points:")
    print("=" * 60)
    for point in hitl_decision_points:
        print(f"\n  Decision Point #{point['id']}: {point['name']}")
        print(f"    Trigger:  {point['trigger'][:100]}")
        print(f"    Model:    {point['hitl_model']}")
        print(f"    Context:  {point['context_needed'][:100]}")
        print(f"    Example:  {point['example'][:100]}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_confidence_router()
    test_hitl_points()
