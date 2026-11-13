"""
Bron status ótiwleri ushın state machine.

Bul modul tekseriw hám audit log penen bronlar ushın anıq status ótiwlerin ámelge asıradı.
"""
from enum import Enum
from typing import Dict, Set, Optional, Tuple


class BookingState(Enum):
    """Bron status jaǵdayları."""
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'
    NO_SHOW = 'no_show'


class BookingStateMachine:
    """
    Bron status ótiwleri ushın state machine.

    Tekseriw penen anıq status ótiwlerin májbúrleydi.
    """

    # Jaramlı status ótiwleri
    TRANSITIONS: Dict[BookingState, Set[BookingState]] = {
        BookingState.PENDING: {BookingState.CONFIRMED, BookingState.CANCELLED},
        BookingState.CONFIRMED: {BookingState.CANCELLED, BookingState.COMPLETED, BookingState.NO_SHOW},
        BookingState.CANCELLED: set(),  # Aqırǵı jaǵday
        BookingState.COMPLETED: set(),  # Aqırǵı jaǵday
        BookingState.NO_SHOW: set(),  # Aqırǵı jaǵday
    }

    # Audit log ushın ótiw sebepleri
    TRANSITION_REASONS: Dict[Tuple[BookingState, BookingState], str] = {
        (BookingState.PENDING, BookingState.CONFIRMED): 'payment_completed',
        (BookingState.PENDING, BookingState.CANCELLED): 'user_cancelled',  # 'expiry' de bolıwı múmkin
        (BookingState.CONFIRMED, BookingState.CANCELLED): 'user_cancelled',
        (BookingState.CONFIRMED, BookingState.COMPLETED): 'checkout_completed',
        (BookingState.CONFIRMED, BookingState.NO_SHOW): 'guest_no_show',
    }

    # TEK belgili bir sebep penen bar bolatuǵın ótiwler (R12): juwmaqlanǵan turıw
    # tek staff mehmanxananıń no-show esabatın tastıyıqlaǵanda no-show boladı. can_transition()
    # olar ushın False qaladı; validate_transition() olardı tek usı sebep penen qabıllaydı.
    GATED_TRANSITIONS: Dict[Tuple[BookingState, BookingState], str] = {
        (BookingState.COMPLETED, BookingState.NO_SHOW): 'no_show_report_approved',
        # staff tastıyıqlanǵan esabattı túzetti: turıw haqıyqatında boldı
        (BookingState.NO_SHOW, BookingState.COMPLETED): 'no_show_report_reversed',
        (BookingState.NO_SHOW, BookingState.CONFIRMED): 'no_show_report_reversed',
    }

    @classmethod
    def can_transition(cls, from_state: BookingState, to_state: BookingState) -> bool:
        """
        Status ótiwiniń jaramlı ekenin tekseriw.

        Argumentler:
            from_state: Házirgi jaǵday
            to_state: Maqset jaǵday

        Qaytaradı:
            bool: Ótiw jaramlı bolsa True
        """
        if from_state == to_state:
            return False  # Óz-ózine ótiw joq

        valid_transitions = cls.TRANSITIONS.get(from_state, set())
        return to_state in valid_transitions

    @classmethod
    def validate_transition(cls, from_state: BookingState, to_state: BookingState,
                          reason: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Status ótiwin tekseriw hám tekseriw nátiyjesin qaytarıw.

        Argumentler:
            from_state: Házirgi jaǵday
            to_state: Maqset jaǵday
            reason: Ótiw ushın ıqtıyarıy sebep

        Qaytaradı:
            tuple: (is_valid, error_message)
        """
        if from_state == to_state:
            return False, f"Cannot transition from {from_state.value} to {to_state.value} (same state)"

        gated_reason = cls.GATED_TRANSITIONS.get((from_state, to_state))
        if gated_reason is not None:
            if reason == gated_reason:
                return True, None
            return False, f"Invalid transition from {from_state.value} to {to_state.value}"

        valid_transitions = cls.TRANSITIONS.get(from_state, set())
        if to_state not in valid_transitions:
            return False, f"Invalid transition from {from_state.value} to {to_state.value}"

        # Berilgen bolsa sebepti tekseriw
        if reason:
            expected_reason = cls.TRANSITION_REASONS.get((from_state, to_state))
            # Ayırım ótiwler ushın bir neshe jaramlı sebepke ruxsat beriw
            if expected_reason:
                # pending->cancelled ushın 'user_cancelled' hám 'expiry' ekewine de ruxsat beriw
                if (from_state, to_state) == (BookingState.PENDING, BookingState.CANCELLED):
                    if reason not in ['user_cancelled', 'expiry']:
                        return False, f"Invalid reason '{reason}' for transition from {from_state.value} to {to_state.value}. Expected: user_cancelled or expiry"
                elif reason != expected_reason:
                    return False, f"Invalid reason '{reason}' for transition from {from_state.value} to {to_state.value}. Expected: {expected_reason}"

        return True, None

    @classmethod
    def get_transition_reason(cls, from_state: BookingState, to_state: BookingState) -> Optional[str]:
        """
        Status ótiwi ushın kútilgen sebepti alıw.

        Argumentler:
            from_state: Házirgi jaǵday
            to_state: Maqset jaǵday

        Qaytaradı:
            str yamasa None: Kútilgen sebep yamasa anıqlanbaǵan bolsa None
        """
        return cls.TRANSITION_REASONS.get((from_state, to_state))

    @classmethod
    def get_valid_transitions(cls, from_state: BookingState) -> Set[BookingState]:
        """
        Berilgen jaǵdaydan barlıq jaramlı ótiwlerdi alıw.
        """
        return cls.TRANSITIONS.get(from_state, set())
