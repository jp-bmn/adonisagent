"""
Task 5 — Tests for app/services/rules_engine.py

Covers all 8 rules with positive and negative cases.
Target: ≥ 90% coverage of rules_engine.py
"""
from __future__ import annotations
import pytest
from app.services.rules_engine import (
    classify_with_rules,
    get_rules_engine_stats,
    RulesEngineResult,
    RULES,
    VALID_SIGNAL_TYPES,
    VALID_TIERS,
)


# ===========================================================================
# Helpers
# ===========================================================================

def classify(title: str, text: str = "") -> RulesEngineResult:
    return classify_with_rules(title=title, text=text)


# ===========================================================================
# Rule 1 — leadership_change
# ===========================================================================

class TestLeadershipChange:

    def test_cro_departure(self):
        r = classify("CRO John Smith departs NewYork-Presbyterian")
        assert r.matched
        assert r.signal_type == "leadership_change"
        assert r.tier == "urgent"
        assert r.confidence >= 0.85

    def test_cfo_appointment(self):
        r = classify("UMass Memorial names new CFO after restructure")
        assert r.matched
        assert r.signal_type == "leadership_change"

    def test_vp_revenue_hire(self):
        r = classify("Ascension hires VP of Revenue Cycle from competitor")
        assert r.matched
        assert r.signal_type == "leadership_change"

    def test_chief_revenue_officer_named(self):
        r = classify("", text="The hospital has named Sarah Chen as Chief Revenue Officer effective January")
        assert r.matched
        assert r.signal_type == "leadership_change"

    def test_cio_steps_down(self):
        r = classify("CIO steps down at UAMS after 7 years")
        assert r.matched
        assert r.signal_type == "leadership_change"

    def test_vp_rcm_sought(self):
        r = classify("", text="CommonSpirit is seeking a new VP RCM to lead revenue operations")
        assert r.matched
        assert r.signal_type == "leadership_change"

    def test_executive_transition(self):
        r = classify("Leadership transition underway at NYP — Chief Financial Officer exits")
        assert r.matched
        assert r.signal_type == "leadership_change"

    def test_no_match_generic_hire(self):
        """Generic 'hospital hires nurses' should not match leadership_change."""
        r = classify("NewYork-Presbyterian hires 200 registered nurses for expansion")
        assert not r.matched or r.signal_type != "leadership_change"


# ===========================================================================
# Rule 2 — post_golive_friction
# ===========================================================================

class TestPostGoliveFriction:

    def test_post_golive_billing_drop(self):
        r = classify("Billing problems emerge at Ascension post go-live")
        assert r.matched
        assert r.signal_type == "post_golive_friction"
        assert r.tier == "urgent"

    def test_denial_rate_spike(self):
        r = classify("", text="Denial rate has spiked 18% after the Epic launch at UMass Memorial")
        assert r.matched
        assert r.signal_type == "post_golive_friction"

    def test_ar_impacted(self):
        r = classify("Accounts receivable impacted following EHR rollout")
        assert r.matched
        assert r.signal_type == "post_golive_friction"

    def test_revenue_fell_after(self):
        r = classify("", text="Revenue dropped 12% after implementing the new system")
        assert r.matched
        assert r.signal_type == "post_golive_friction"

    def test_cash_flow_concern(self):
        r = classify("Cash flow worsened since Epic EMR deployment at UAMS")
        assert r.matched
        assert r.signal_type == "post_golive_friction"


# ===========================================================================
# Rule 3 — epic_go_live
# ===========================================================================

class TestEpicGoLive:

    def test_epic_go_live_direct(self):
        r = classify("Ascension goes live on Epic EHR across 14 facilities")
        assert r.matched
        assert r.signal_type == "epic_go_live"
        assert r.tier == "urgent"

    def test_ehr_launch(self):
        r = classify("", text="CommonSpirit announces EHR go-live date set for Q3")
        assert r.matched
        assert r.signal_type == "epic_go_live"

    def test_cerner_golive(self):
        r = classify("UAMS Cerner implementation go-live scheduled for March")
        assert r.matched
        assert r.signal_type == "epic_go_live"

    def test_meditech_deploy(self):
        r = classify("Hospital deploys Meditech system across network")
        assert r.matched
        assert r.signal_type == "epic_go_live"

    def test_electronic_health_record_implement(self):
        r = classify("", text="Electronic health record implementation begins at NYP next month")
        assert r.matched
        assert r.signal_type == "epic_go_live"


# ===========================================================================
# Rule 4 — ma_acquisition
# ===========================================================================

class TestMaAcquisition:

    def test_acquired_by(self):
        r = classify("Regional hospital acquired by CommonSpirit Health")
        assert r.matched
        assert r.signal_type == "ma_acquisition"
        assert r.tier == "urgent"

    def test_merger(self):
        r = classify("Ascension and MidWest Regional announce merger agreement")
        assert r.matched
        assert r.signal_type == "ma_acquisition"

    def test_acquisition_direct(self):
        r = classify("NewYork-Presbyterian completes acquisition of Hudson Valley Health")
        assert r.matched
        assert r.signal_type == "ma_acquisition"

    def test_joint_venture(self):
        r = classify("", text="UMass Memorial enters joint venture with Boston hospital network")
        assert r.matched
        assert r.signal_type == "ma_acquisition"

    def test_negative_talent_acquisition(self):
        """'talent acquisition' is an HR term, not M&A."""
        r = classify("Hospital improves talent acquisition strategy for nursing staff")
        assert not r.matched or r.signal_type != "ma_acquisition"

    def test_negative_customer_acquisition(self):
        r = classify("Healthcare company improves customer acquisition funnel")
        assert not r.matched or r.signal_type != "ma_acquisition"


# ===========================================================================
# Rule 5 — restructuring
# ===========================================================================

class TestRestructuring:

    def test_layoffs(self):
        r = classify("UAMS announces layoffs affecting 300 employees")
        assert r.matched
        assert r.signal_type == "restructuring"
        assert r.tier == "urgent"

    def test_workforce_reduction(self):
        r = classify("Ascension to reduce workforce by 8% citing financial pressure")
        assert r.matched
        assert r.signal_type == "restructuring"

    def test_restructuring_direct(self):
        r = classify("CommonSpirit Health restructuring operations in Midwest division")
        assert r.matched
        assert r.signal_type == "restructuring"

    def test_position_eliminated(self):
        r = classify("", text="Hospital eliminates 45 positions in billing department consolidation")
        assert r.matched
        assert r.signal_type == "restructuring"

    def test_department_closing(self):
        r = classify("NYP closing outpatient department amid budget cuts")
        assert r.matched
        assert r.signal_type == "restructuring"

    def test_negative_financial_restructuring(self):
        """Debt/bond restructuring is a financial event, not workforce."""
        r = classify("Hospital restructuring $200M in bond debt with new terms")
        assert not r.matched or r.signal_type != "restructuring"


# ===========================================================================
# Rule 6 — rcm_hiring_spike
# ===========================================================================

class TestRcmHiringSpike:

    def test_rcm_hiring(self):
        r = classify("UMass Memorial hiring 12 RCM specialists this quarter")
        assert r.matched
        assert r.signal_type == "rcm_hiring_spike"
        assert r.tier == "urgent"

    def test_revenue_cycle_positions(self):
        r = classify("", text="Revenue cycle coordinator positions open at Ascension — 8 roles posted")
        assert r.matched
        assert r.signal_type == "rcm_hiring_spike"

    def test_billing_analyst_wanted(self):
        r = classify("Seeking experienced billing analyst for NYP revenue team")
        assert r.matched
        assert r.signal_type == "rcm_hiring_spike"

    def test_director_rcm_search(self):
        r = classify("CommonSpirit searching for Director of Revenue Cycle Management")
        assert r.matched
        assert r.signal_type == "rcm_hiring_spike"


# ===========================================================================
# Rule 7 — vendor_change
# ===========================================================================

class TestVendorChange:

    def test_switching_vendor(self):
        r = classify("Ascension switching RCM vendor after contract dispute")
        assert r.matched
        assert r.signal_type == "vendor_change"
        assert r.tier == "urgent"

    def test_replacing_platform(self):
        r = classify("", text="UAMS replacing current billing platform with new solution")
        assert r.matched
        assert r.signal_type == "vendor_change"

    def test_contract_terminated(self):
        r = classify("NYP terminates vendor contract for patient billing software")
        assert r.matched
        assert r.signal_type == "vendor_change"

    def test_new_vendor_selected(self):
        r = classify("CommonSpirit selects new technology partner for revenue operations")
        assert r.matched
        assert r.signal_type == "vendor_change"

    def test_vendor_lawsuit(self):
        r = classify("UMass Memorial sues vendor over billing system failures")
        assert r.matched
        assert r.signal_type == "vendor_change"


# ===========================================================================
# Rule 8 — financial_event
# ===========================================================================

class TestFinancialEvent:

    def test_operating_loss(self):
        r = classify("NYP reports $45M operating loss for fiscal year")
        assert r.matched
        assert r.signal_type == "financial_event"
        assert r.tier == "worth_knowing"

    def test_budget_cuts(self):
        r = classify("Ascension announces budget cuts across all service lines")
        assert r.matched
        assert r.signal_type == "financial_event"

    def test_credit_downgrade(self):
        r = classify("", text="Moody's downgrades UAMS credit rating to Baa2 on financial concerns")
        assert r.matched
        assert r.signal_type == "financial_event"

    def test_revenue_declined(self):
        r = classify("CommonSpirit revenue declined 9% as patient volumes fell")
        assert r.matched
        assert r.signal_type == "financial_event"

    def test_annual_report(self):
        r = classify("UMass Memorial releases annual report showing cash flow concerns")
        assert r.matched
        assert r.signal_type == "financial_event"

    def test_negative_revenue_cycle_context(self):
        """'revenue cycle' mentions should not trigger financial_event."""
        r = classify("Hospital improving revenue cycle processes to boost collection")
        assert not r.matched or r.signal_type != "financial_event"


# ===========================================================================
# No match — falls through to Claude
# ===========================================================================

class TestNoMatch:

    def test_community_event(self):
        r = classify("NewYork-Presbyterian hosts annual community health fair")
        assert not r.matched

    def test_generic_expansion(self):
        r = classify("Hospital opens new outpatient clinic in suburban location")
        assert not r.matched

    def test_empty_text(self):
        r = classify(title="", text="")
        assert not r.matched

    def test_unrelated_news(self):
        r = classify("Local sports team partners with hospital for athlete care")
        assert not r.matched


# ===========================================================================
# RulesEngineResult dataclass
# ===========================================================================

class TestRulesEngineResult:

    def test_bool_true_when_matched(self):
        r = RulesEngineResult(matched=True, signal_type="leadership_change", tier="urgent", confidence=0.9)
        assert bool(r) is True

    def test_bool_false_when_not_matched(self):
        r = RulesEngineResult(matched=False)
        assert bool(r) is False

    def test_default_matched_keywords_empty(self):
        r = RulesEngineResult(matched=False)
        assert r.matched_keywords == []


# ===========================================================================
# get_rules_engine_stats
# ===========================================================================

class TestRulesEngineStats:

    def test_returns_dict(self):
        stats = get_rules_engine_stats()
        assert isinstance(stats, dict)

    def test_rule_count_matches(self):
        stats = get_rules_engine_stats()
        assert stats["rule_count"] == len(RULES)

    def test_all_rule_names_present(self):
        stats = get_rules_engine_stats()
        for rule in RULES:
            assert rule.name in stats["rules"]

    def test_signal_types_are_valid(self):
        stats = get_rules_engine_stats()
        for st in stats["signal_types"]:
            assert st in VALID_SIGNAL_TYPES

    def test_tiers_are_valid(self):
        stats = get_rules_engine_stats()
        for tier in stats["valid_tiers"]:
            assert tier in VALID_TIERS
