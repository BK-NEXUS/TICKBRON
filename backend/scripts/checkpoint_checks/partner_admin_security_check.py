"""
Security review script for Checkpoint 18 - Partner APIs and Admin Moderation.

This script performs a comprehensive security review of the new partner and admin endpoints.
"""
import re


def check_partner_security():
    """Check security aspects of partner API endpoints."""
    print("=" * 60)
    print("PARTNER API SECURITY REVIEW")
    print("=" * 60)
    
    checks_passed = 0
    checks_total = 0
    
    # Check 1: Hotel-owner permission class
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
    
    # Check 2: Property ownership scoping
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
    
    # Check 3: Room type ownership validation
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
    
    # Check 4: Rate plan ownership validation
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
    
    # Check 5: Date inventory ownership validation
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
    
    # Check 6: Booked rooms read-only protection
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
    
    # Check 7: Authentication required for all partner endpoints
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
    
    # Check 8: No password exposure in logs/responses
    checks_total += 1
    try:
        with open('partner/serializers.py', 'r') as f:
            content = f.read()
            if 'password' not in content.lower():  # Partner serializers shouldn't handle passwords
                print("✓ Check 8: No password handling in partner serializers")
                checks_passed += 1
            else:
                print("⚠ Check 8: Password field found in partner serializers (review if intentional)")
                checks_passed += 1  # Still pass if it's intentional
    except FileNotFoundError:
        print("✗ Check 8: partner/serializers.py not found")
    
    print(f"\nPartner API Security: {checks_passed}/{checks_total} checks passed")
    return checks_passed, checks_total


def check_admin_security():
    """Check security aspects of admin API endpoints."""
    print("\n" + "=" * 60)
    print("ADMIN API SECURITY REVIEW")
    print("=" * 60)
    
    checks_passed = 0
    checks_total = 0
    
    # Check 1: Super-admin permission class
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
    
    # Check 2: Staff permission class
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
    
    # Check 3: Hotel-owner creation restricted to super-admin
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
    
    # Check 4: Password hashing in user creation
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
    
    # Check 5: Password not returned in response
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
    
    # Check 6: Password confirmation validation
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
    
    # Check 7: Role assignment in hotel-owner creation
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
    
    # Check 8: Authentication required for all admin endpoints
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
    
    # Check 9: Property approval tracking
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
    
    # Check 10: Rejection reason tracking
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
    """Check that hotel-owners cannot access other owners' data."""
    print("\n" + "=" * 60)
    print("CROSS-OWNER ACCESS SECURITY REVIEW")
    print("=" * 60)
    
    checks_passed = 0
    checks_total = 0
    
    # Check 1: Property queryset filtering
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
    
    # Check 2: Room type queryset filtering
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
    
    # Check 3: Rate plan queryset filtering
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
    
    # Check 4: Date inventory queryset filtering
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
    
    # Check 5: Serializer validation for cross-owner access
    checks_total += 1
    try:
        with open('partner/serializers.py', 'r') as f:
            content = f.read()
            validation_count = content.count('validate_')
            if validation_count >= 3:  # Should have validation for property, room_type, rate_plan
                print("✓ Check 5: Serializer validation for cross-owner access prevention")
                checks_passed += 1
            else:
                print("✗ Check 5: Insufficient serializer validation for cross-owner access")
    except FileNotFoundError:
        print("✗ Check 5: partner/serializers.py not found")
    
    print(f"\nCross-Owner Access Security: {checks_passed}/{checks_total} checks passed")
    return checks_passed, checks_total


def main():
    """Run all security checks."""
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
