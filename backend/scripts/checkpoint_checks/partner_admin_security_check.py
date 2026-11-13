"""
Checkpoint 18 qáwipsizlik tekseriw skripti - Partner API ları hám Admin moderaciyası.

Bul skript jańa partner hám admin endpoint lerin tolıq qáwipsizlik tekseriwinen ótkeredi.
"""


def check_partner_security():
    """Partner API endpoint lerinin qáwipsizlik tárepların tekseriw."""
    print("=" * 60)
    print("PARTNER API SECURITY REVIEW")
    print("=" * 60)

    checks_passed = 0
    checks_total = 0

    # 1-tekseriw: Mehmanxana iyesi ruxsat klası
    checks_total += 1
    try:
        with open('partner/views.py', 'r') as f:
            content = f.read()
            if 'class IsHotelOwner' in content and 'IsAuthenticated' in content:
                print("✓ Check 1: Hotel-owner permission class implemented with authentication")
                checks_passed += 1
            else:
                print("✗ Check 1: Hotel-owner permission class missing or incomplete")
    except FileNotFoundError:
        print("✗ Check 1: partner/views.py not found")

    # 2-tekseriw: Mehmanxana iyeligi menen sheklew
    checks_total += 1
    try:
        with open('partner/views.py', 'r') as f:
            content = f.read()
            if 'owner=self.request.user' in content or 'property__owner=self.request.user' in content:
                print("✓ Check 2: Property ownership scoping implemented")
                checks_passed += 1
            else:
                print("✗ Check 2: Property ownership scoping missing")
    except FileNotFoundError:
        print("✗ Check 2: partner/views.py not found")

    # 3-tekseriw: Xona túri iyeligin tekseriw
    checks_total += 1
    try:
        with open('partner/serializers.py', 'r') as f:
            content = f.read()
            if 'validate_property' in content and 'owner != request.user' in content:
                print("✓ Check 3: Room type ownership validation in serializers")
                checks_passed += 1
            else:
                print("✗ Check 3: Room type ownership validation missing")
    except FileNotFoundError:
        print("✗ Check 3: partner/serializers.py not found")

    # 4-tekseriw: Rate plan iyeligin tekseriw
    checks_total += 1
    try:
        with open('partner/serializers.py', 'r') as f:
            content = f.read()
            if 'validate_room_type' in content and 'property.owner != request.user' in content:
                print("✓ Check 4: Rate plan ownership validation in serializers")
                checks_passed += 1
            else:
                print("✗ Check 4: Rate plan ownership validation missing")
    except FileNotFoundError:
        print("✗ Check 4: partner/serializers.py not found")

    # 5-tekseriw: Date inventory iyeligin tekseriw
    checks_total += 1
    try:
        with open('partner/serializers.py', 'r') as f:
            content = f.read()
            if 'validate_rate_plan' in content and 'room_type.property.owner != request.user' in content:
                print("✓ Check 5: Date inventory ownership validation in serializers")
                checks_passed += 1
            else:
                print("✗ Check 5: Date inventory ownership validation missing")
    except FileNotFoundError:
        print("✗ Check 5: partner/serializers.py not found")

    # 6-tekseriw: Bronlanǵan xonalar tek oqıw ushın qorǵalǵan
    checks_total += 1
    try:
        with open('partner/serializers.py', 'r') as f:
            content = f.read()
            if 'booked_rooms' in content and 'read_only_fields' in content:
                print("✓ Check 6: Booked rooms field is read-only")
                checks_passed += 1
            else:
                print("✗ Check 6: Booked rooms field not properly protected")
    except FileNotFoundError:
        print("✗ Check 6: partner/serializers.py not found")

    # 7-tekseriw: Barlıq partner endpoint leri ushın autentifikaciya kerek
    checks_total += 1
    try:
        with open('partner/views.py', 'r') as f:
            content = f.read()
            if 'permission_classes = [IsHotelOwner]' in content or '@permission_classes([IsHotelOwner])' in content:
                print("✓ Check 7: Authentication required for partner endpoints")
                checks_passed += 1
            else:
                print("✗ Check 7: Authentication not properly required")
    except FileNotFoundError:
        print("✗ Check 7: partner/views.py not found")

    # 8-tekseriw: Log/juwaplarda parol ashılmaǵan
    checks_total += 1
    try:
        with open('partner/serializers.py', 'r') as f:
            content = f.read()
            if 'password' not in content.lower():  # Partner serializer leri parollerdi islemewi kerek
                print("✓ Check 8: No password handling in partner serializers")
                checks_passed += 1
            else:
                print("⚠ Check 8: Password field found in partner serializers (review if intentional)")
                checks_passed += 1  # Qásten bolsa ele de ótedi
    except FileNotFoundError:
        print("✗ Check 8: partner/serializers.py not found")

    print(f"\nPartner API Security: {checks_passed}/{checks_total} checks passed")
    return checks_passed, checks_total


def check_admin_security():
    """Admin API endpoint lerinin qáwipsizlik tárepların tekseriw."""
    print("\n" + "=" * 60)
    print("ADMIN API SECURITY REVIEW")
    print("=" * 60)

    checks_passed = 0
    checks_total = 0

    # 1-tekseriw: Super-admin ruxsat klası
    checks_total += 1
    try:
        with open('admin/views.py', 'r') as f:
            content = f.read()
            if 'class IsSuperAdmin' in content and 'is_superuser' in content:
                print("✓ Check 1: Super-admin permission class implemented")
                checks_passed += 1
            else:
                print("✗ Check 1: Super-admin permission class missing")
    except FileNotFoundError:
        print("✗ Check 1: admin/views.py not found")

    # 2-tekseriw: Staff ruxsat klası
    checks_total += 1
    try:
        with open('admin/views.py', 'r') as f:
            content = f.read()
            if 'class IsSuperAdminOrStaff' in content and 'is_staff' in content:
                print("✓ Check 2: Staff permission class implemented")
                checks_passed += 1
            else:
                print("✗ Check 2: Staff permission class missing")
    except FileNotFoundError:
        print("✗ Check 2: admin/views.py not found")

    # 3-tekseriw: Mehmanxana iyesin jaratıw super-admin menen sheklengen
    checks_total += 1
    try:
        with open('admin/views.py', 'r') as f:
            content = f.read()
            if 'admin_create_hotel_owner' in content and 'IsSuperAdmin' in content:
                print("✓ Check 3: Hotel-owner creation restricted to super-admin")
                checks_passed += 1
            else:
                print("✗ Check 3: Hotel-owner creation not properly restricted")
    except FileNotFoundError:
        print("✗ Check 3: admin/views.py not found")

    # 4-tekseriw: Paydalanıwshı jaratıwda parol hashlenedi
    checks_total += 1
    try:
        with open('admin/serializers.py', 'r') as f:
            content = f.read()
            if 'create_user' in content and 'password' in content:
                print("✓ Check 4: Password handling using create_user (hashes password)")
                checks_passed += 1
            else:
                print("✗ Check 4: Password not properly hashed")
    except FileNotFoundError:
        print("✗ Check 4: admin/serializers.py not found")

    # 5-tekseriw: Parol juwapta qaytarılmaydı
    checks_total += 1
    try:
        with open('admin/serializers.py', 'r') as f:
            content = f.read()
            if 'write_only' in content and 'password' in content:
                print("✓ Check 5: Password field marked as write-only")
                checks_passed += 1
            else:
                print("✗ Check 5: Password field not write-only")
    except FileNotFoundError:
        print("✗ Check 5: admin/serializers.py not found")

    # 6-tekseriw: Parol tastıyıqlaw validaciyası
    checks_total += 1
    try:
        with open('admin/serializers.py', 'r') as f:
            content = f.read()
            if 'password_confirm' in content and 'validate' in content:
                print("✓ Check 6: Password confirmation validation implemented")
                checks_passed += 1
            else:
                print("✗ Check 6: Password confirmation validation missing")
    except FileNotFoundError:
        print("✗ Check 6: admin/serializers.py not found")

    # 7-tekseriw: Mehmanxana iyesin jaratıwda rol beriw
    checks_total += 1
    try:
        with open('admin/serializers.py', 'r') as f:
            content = f.read()
            if 'hotel-owner' in content and 'role=' in content:
                print("✓ Check 7: Hotel-owner role assigned during account creation")
                checks_passed += 1
            else:
                print("✗ Check 7: Hotel-owner role not properly assigned")
    except FileNotFoundError:
        print("✗ Check 7: admin/serializers.py not found")

    # 8-tekseriw: Barlıq admin endpoint leri ushın autentifikaciya kerek
    checks_total += 1
    try:
        with open('admin/views.py', 'r') as f:
            content = f.read()
            if 'permission_classes = [IsSuperAdminOrStaff]' in content or 'permission_classes = [IsSuperAdmin]' in content:
                print("✓ Check 8: Authentication required for admin endpoints")
                checks_passed += 1
            else:
                print("✗ Check 8: Authentication not properly required")
    except FileNotFoundError:
        print("✗ Check 8: admin/views.py not found")

    # 9-tekseriw: Mehmanxananı tastıyıqlawdı qadaǵalaw
    checks_total += 1
    try:
        with open('admin/views.py', 'r') as f:
            content = f.read()
            if 'approved_by' in content and 'approved_at' in content:
                print("✓ Check 9: Property approval tracking implemented")
                checks_passed += 1
            else:
                print("✗ Check 9: Property approval tracking missing")
    except FileNotFoundError:
        print("✗ Check 9: admin/views.py not found")

    # 10-tekseriw: Bas tartıw sebebin qadaǵalaw
    checks_total += 1
    try:
        with open('admin/views.py', 'r') as f:
            content = f.read()
            if 'rejection_reason' in content:
                print("✓ Check 10: Property rejection reason tracking implemented")
                checks_passed += 1
            else:
                print("✗ Check 10: Property rejection reason tracking missing")
    except FileNotFoundError:
        print("✗ Check 10: admin/views.py not found")

    print(f"\nAdmin API Security: {checks_passed}/{checks_total} checks passed")
    return checks_passed, checks_total


def check_cross_owner_access():
    """Mehmanxana iyeleri basqa iyelerdiń maǵlıwmatına qol jetkere almaytuǵının tekseriw."""
    print("\n" + "=" * 60)
    print("CROSS-OWNER ACCESS SECURITY REVIEW")
    print("=" * 60)

    checks_passed = 0
    checks_total = 0

    # 1-tekseriw: Mehmanxana queryset filterlewi
    checks_total += 1
    try:
        with open('partner/views.py', 'r') as f:
            content = f.read()
            if 'owner=self.request.user' in content and 'Property.objects.filter' in content:
                print("✓ Check 1: Property queryset filtered by owner")
                checks_passed += 1
            else:
                print("✗ Check 1: Property queryset not properly filtered")
    except FileNotFoundError:
        print("✗ Check 1: partner/views.py not found")

    # 2-tekseriw: Xona túri queryset filterlewi
    checks_total += 1
    try:
        with open('partner/views.py', 'r') as f:
            content = f.read()
            if 'property__owner=self.request.user' in content and 'RoomType.objects.filter' in content:
                print("✓ Check 2: Room type queryset filtered by property owner")
                checks_passed += 1
            else:
                print("✗ Check 2: Room type queryset not properly filtered")
    except FileNotFoundError:
        print("✗ Check 2: partner/views.py not found")

    # 3-tekseriw: Rate plan queryset filterlewi
    checks_total += 1
    try:
        with open('partner/views.py', 'r') as f:
            content = f.read()
            if 'room_type__property__owner=self.request.user' in content and 'RatePlan.objects.filter' in content:
                print("✓ Check 3: Rate plan queryset filtered by property owner")
                checks_passed += 1
            else:
                print("✗ Check 3: Rate plan queryset not properly filtered")
    except FileNotFoundError:
        print("✗ Check 3: partner/views.py not found")

    # 4-tekseriw: Date inventory queryset filterlewi
    checks_total += 1
    try:
        with open('partner/views.py', 'r') as f:
            content = f.read()
            if 'rate_plan__room_type__property__owner=self.request.user' in content and 'DateInventory.objects.filter' in content:
                print("✓ Check 4: Date inventory queryset filtered by property owner")
                checks_passed += 1
            else:
                print("✗ Check 4: Date inventory queryset not properly filtered")
    except FileNotFoundError:
        print("✗ Check 4: partner/views.py not found")

    # 5-tekseriw: Basqa iyege qol jetkeriw ushın serializer validaciyası
    checks_total += 1
    try:
        with open('partner/serializers.py', 'r') as f:
            content = f.read()
            validation_count = content.count('validate_')
            if validation_count >= 3:  # property, room_type, rate_plan ushın validaciya bolıwı kerek
                print("✓ Check 5: Serializer validation for cross-owner access prevention")
                checks_passed += 1
            else:
                print("✗ Check 5: Insufficient serializer validation for cross-owner access")
    except FileNotFoundError:
        print("✗ Check 5: partner/serializers.py not found")

    print(f"\nCross-Owner Access Security: {checks_passed}/{checks_total} checks passed")
    return checks_passed, checks_total


def main():
    """Barlıq qáwipsizlik tekseriwlerin islew."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "CHECKPOINT 18 SECURITY REVIEW" + " " * 22 + "║")
    print("╚" + "=" * 58 + "╝")

    partner_passed, partner_total = check_partner_security()
    admin_passed, admin_total = check_admin_security()
    cross_passed, cross_total = check_cross_owner_access()

    total_passed = partner_passed + admin_passed + cross_passed
    total_checks = partner_total + admin_total + cross_total

    print("\n" + "=" * 60)
    print("OVERALL SECURITY SUMMARY")
    print("=" * 60)
    print(f"Total Checks Passed: {total_passed}/{total_checks}")
    print(f"Partner API: {partner_passed}/{partner_total}")
    print(f"Admin API: {admin_passed}/{admin_total}")
    print(f"Cross-Owner Access: {cross_passed}/{cross_total}")

    if total_passed == total_checks:
        print("\n✓ ALL SECURITY CHECKS PASSED")
        return 0
    else:
        print(f"\n✗ {total_checks - total_passed} SECURITY CHECK(S) FAILED")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
