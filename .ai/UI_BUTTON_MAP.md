# UI button map (2026-11-01)

What each screen reads and writes. Generated from the code (`frontend/src/pages`, `components`, `layout`): the
"Buttons" and "Links" columns count `<Button>/<button>` and `<Link>/<a>` elements in the file; the last column lists the
adapter calls the file makes and the backend endpoint each one hits. A call without an arrow is a list/read request whose
URL is built from filters (page, search, letter, dates); its endpoint is the adapter method of the same name in
`frontend/src/adapters/`. Every write goes through an adapter, never straight from a component, and the backend decides
permissions, totals and availability.

Reading rule: a button either navigates (Link), changes local state (filters, tabs, dialogs), or calls an adapter method
in the table. The crawler `frontend/e2e/crawl.e2e.ts` presses every safe button of guest, owner and admin at 390 and
1440 px and fails on dead buttons, 404s and console errors.

| File | Buttons | Links | Reads/writes (adapter → endpoint) |
|---|---|---|---|
| `components/AdminAmenityManagement.tsx` | 11 | 0 | adminAdapter.createAmenity → POST /api/v1/admin-panel/amenities/<br>adminAdapter.createAmenityCategory → POST /api/v1/admin-panel/amenities/categories/<br>adminAdapter.deleteAmenity → DELETE /api/v1/admin-panel/amenities/{x}/<br>adminAdapter.deleteAmenityCategory → DELETE /api/v1/admin-panel/amenities/categories/{x}/<br>adminAdapter.getAmenities → GET /api/v1/admin-panel/amenities/<br>adminAdapter.getAmenityCategories → GET /api/v1/admin-panel/amenities/categories/<br>adminAdapter.updateAmenity → PATCH /api/v1/admin-panel/amenities/{x}/<br>adminAdapter.updateAmenityCategory → PATCH /api/v1/admin-panel/amenities/categories/{x}/ |
| `components/AdminCommission.tsx` | 4 | 0 | adminAdapter.confirmCommissionMonth → POST /api/v1/admin-panel/commission/{x}/months/{x}/paid/<br>adminAdapter.getCommissionOwners → GET /api/v1/admin-panel/commission/<br>adminAdapter.getCommissionStatement → GET /api/v1/admin-panel/commission/{x}/<br>adminAdapter.setCommissionPercent → PUT /api/v1/admin-panel/commission/{x}/rate/<br>adminAdapter.undoCommissionMonth → DELETE /api/v1/admin-panel/commission/{x}/months/{x}/paid/ |
| `components/AdminCustomerProfile.tsx` | 6 | 2 | adminAdapter.createInternalNote → POST /api/v1/admin-panel/customers/{x}/notes/<br>adminAdapter.deleteInternalNote → DELETE /api/v1/admin-panel/customers/{x}/notes/{x}/<br>adminAdapter.getCustomerProfile<br>adminAdapter.updateInternalNote → PUT /api/v1/admin-panel/customers/{x}/notes/{x}/ |
| `components/AdminCustomersList.tsx` | 3 | 2 | adminAdapter.getCustomers |
| `components/AdminExchangeRates.tsx` | 4 | 0 | exchangeRateAdapter.accept → POST {x}/accept/<br>exchangeRateAdapter.list<br>exchangeRateAdapter.status |
| `components/AdminGeography.tsx` | 12 | 0 | adminGeographyAdapter.list<br>adminGeographyAdapter.remove<br>adminGeographyAdapter.reorder<br>adminGeographyAdapter.update |
| `components/AdminNoShowReports.tsx` | 4 | 0 | noShowAdapter.listReports |
| `components/AdminPromotionRenewals.tsx` | 5 | 1 | promotionAdapter.confirmRenewal → GET {x}/promotions/renewals/{x}/confirm/<br>promotionAdapter.declineRenewal → GET {x}/promotions/renewals/{x}/decline/<br>promotionAdapter.listRenewals → GET {x}/promotions/renewals/ |
| `components/AdminPromotions.tsx` | 7 | 0 | promotionAdapter.listPromotions → GET {x}/promotions/<br>promotionAdapter.markPromotionPaid → GET {x}/promotions/{x}/mark-paid/<br>promotionAdapter.pausePromotion → GET {x}/promotions/{x}/pause/<br>promotionAdapter.resumePromotion → GET {x}/promotions/{x}/resume/ |
| `components/AdminPropertyModeration.tsx` | 6 | 0 | adminAdapter.approveProperty → POST /api/v1/admin-panel/properties/{x}/approve/<br>adminAdapter.getProperties → GET /api/v1/admin-panel/properties/<br>adminAdapter.suspendProperty → POST /api/v1/admin-panel/properties/{x}/suspend/ |
| `components/AdminReviewModeration.tsx` | 4 | 0 | adminAdapter.decideReview → POST /api/v1/admin-panel/reviews/{x}/{x}/<br>adminAdapter.getReviews → GET /api/v1/admin-panel/reviews/ |
| `components/AdminStatisticsDashboard.tsx` | 0 | 0 | adminAdapter.getRegistrationStatistics |
| `components/AdminStatusHotels.tsx` | 0 | 0 | statusAdapter.exportAdminHotels<br>statusAdapter.getAdminHotels → GET {x}/hotels/{x}/ |
| `components/AdminStatusOverview.tsx` | 1 | 0 | statusAdapter.getAdminOverview |
| `components/AdminStatusSection.tsx` | 4 | 0 | statusAdapter.getCountries → GET {x}/countries/{x}/<br>statusAdapter.getHotels → GET {x}/countries/{x}/regions/{x}/hotels/{x}/<br>statusAdapter.getRegions → GET {x}/countries/{x}/regions/{x}/<br>statusAdapter.getUsers → GET {x}/users/{x}/ |
| `components/AdminSupportChat.tsx` | 3 | 0 | chatAdapter.inbox<br>chatAdapter.thread → GET {x}/conversations/{x}/ |
| `components/AdminUserManagement.tsx` | 6 | 0 | adminAdapter.changeContact → PATCH /api/v1/admin-panel/users/{x}/contact/<br>adminAdapter.getUsers → GET /api/v1/admin-panel/users/<br>adminAdapter.resetTwoFactor → POST /api/v1/admin-panel/users/{x}/2fa-reset/ |
| `components/AlphabetFilter.tsx` | 4 | 0 | — |
| `components/Breadcrumbs.tsx` | 2 | 1 | — |
| `components/Button.tsx` | 1 | 1 | — |
| `components/CancelBookingDialog.tsx` | 2 | 0 | bookingAdapter.cancelBooking → POST /api/v1/bookings/{x}/cancel/ |
| `components/ChangePasswordForm.tsx` | 1 | 0 | authAdapter.changePassword → GET /api/v1/auth/password/change/ |
| `components/ChatThread.tsx` | 1 | 0 | — |
| `components/CoachMark.tsx` | 1 | 0 | — |
| `components/CommissionStatement.tsx` | 2 | 0 | — |
| `components/ContactLink.tsx` | 0 | 1 | — |
| `components/CreateHotelOwnerAccount.tsx` | 5 | 0 | adminAdapter.createAdmin → POST /api/v1/admin-panel/users/create-admin/<br>adminAdapter.createHotelOwner → POST /api/v1/admin-panel/users/create-hotel-owner/ |
| `components/CurrencySelector.tsx` | 2 | 0 | — |
| `components/DateRangeCalendar.tsx` | 2 | 0 | — |
| `components/EmailCodeForm.tsx` | 3 | 0 | — |
| `components/EmptyState.tsx` | 1 | 1 | — |
| `components/ErrorFallback.tsx` | 1 | 0 | — |
| `components/FavoriteButton.tsx` | 1 | 0 | — |
| `components/Footer.tsx` | 0 | 8 | — |
| `components/GeographyPicker.tsx` | 1 | 0 | geographyAdapter.getCities → GET /api/v1/geography/regions/{x}/cities/<br>geographyAdapter.getCountries → GET /api/v1/geography/countries/<br>geographyAdapter.getRegions → GET /api/v1/geography/countries/{x}/regions/ |
| `components/GeographyRowDialog.tsx` | 2 | 0 | adminGeographyAdapter.create<br>adminGeographyAdapter.update |
| `components/Header.tsx` | 3 | 10 | — |
| `components/HomeHotelSection.tsx` | 0 | 1 | propertyAdapter.searchProperties |
| `components/HomePropertyTypes.tsx` | 0 | 1 | propertyAdapter.getFilterOptions → GET /api/v1/properties/filter-options/ |
| `components/HomeWhereTo.tsx` | 3 | 1 | geographyAdapter.getCountries → GET /api/v1/geography/countries/<br>geographyAdapter.getRegions → GET /api/v1/geography/countries/{x}/regions/ |
| `components/LanguageSelector.tsx` | 2 | 0 | — |
| `components/LocationPicker.tsx` | 1 | 0 | — |
| `components/MobileBottomNavigation.tsx` | 0 | 1 | — |
| `components/MobileMenu.tsx` | 1 | 3 | — |
| `components/NoShowDecisionDialog.tsx` | 2 | 0 | — |
| `components/NoShowReportDialog.tsx` | 2 | 0 | noShowAdapter.reportNoShow → GET {x}/bookings/{x}/no-show-report/ |
| `components/PartnerAds.tsx` | 2 | 0 | partnerAdapter.getPromotions → GET /api/v1/partner/promotions/ |
| `components/PartnerArrivals.tsx` | 1 | 1 | partnerAdapter.markGuestArrived → POST /api/v1/partner/bookings/{x}/arrived/<br>statusAdapter.getPartnerArrivals |
| `components/PartnerAvailabilityManagement.tsx` | 10 | 0 | partnerAdapter.bulkSetPrice → POST /api/v1/partner/inventory/bulk-price/<br>partnerAdapter.createDateInventory → POST /api/v1/partner/inventory/<br>partnerAdapter.deleteDateInventory → DELETE /api/v1/partner/inventory/{x}/<br>partnerAdapter.getDateInventory<br>partnerAdapter.updateDateInventory → PATCH /api/v1/partner/inventory/{x}/ |
| `components/PartnerBookingsView.tsx` | 1 | 0 | partnerAdapter.getPartnerBookings<br>statusAdapter.exportPartnerBookings |
| `components/PartnerCommission.tsx` | 1 | 0 | partnerAdapter.getCommission → GET /api/v1/partner/commission/ |
| `components/PartnerHotelStatus.tsx` | 1 | 0 | statusAdapter.getPartnerHotel → GET {x}/hotels/{x}/{x}/ |
| `components/PartnerNoShowReports.tsx` | 2 | 0 | noShowAdapter.listMyReports → GET {x}/no-show-reports/<br>noShowAdapter.withdrawReport → GET {x}/no-show-reports/{x}/withdraw/ |
| `components/PartnerPhotoManager.tsx` | 4 | 0 | — |
| `components/PartnerPhotosManagement.tsx` | 0 | 0 | partnerAdapter.deletePropertyPhoto → DELETE /api/v1/partner/properties/{x}/photos/{x}/<br>partnerAdapter.getPropertyPhotos → GET /api/v1/partner/properties/{x}/photos/<br>partnerAdapter.updatePropertyPhoto → PATCH /api/v1/partner/properties/{x}/photos/{x}/<br>partnerAdapter.uploadPropertyPhoto → GET /api/v1/partner/properties/{x}/photos/ |
| `components/PartnerPropertyEdit.tsx` | 1 | 0 | partnerAdapter.updateProperty → PATCH /api/v1/partner/properties/{x}/ |
| `components/PartnerPropertyWizard.tsx` | 4 | 0 | partnerAdapter.createProperty → POST /api/v1/partner/properties/<br>partnerAdapter.getAssignedPlace → GET /api/v1/partner/assigned-place/<br>partnerAdapter.getPropertyTypes → GET /api/v1/partner/property-types/ |
| `components/PartnerRatesManagement.tsx` | 6 | 0 | partnerAdapter.createRatePlan → POST /api/v1/partner/rates/<br>partnerAdapter.deleteRatePlan → DELETE /api/v1/partner/rates/{x}/<br>partnerAdapter.getRatePlans → GET /api/v1/partner/rates/<br>partnerAdapter.updateRatePlan → PATCH /api/v1/partner/rates/{x}/ |
| `components/PartnerReviews.tsx` | 3 | 0 | partnerAdapter.deleteReviewReply → DELETE /api/v1/partner/reviews/{x}/reply/<br>partnerAdapter.getReviews → GET /api/v1/partner/reviews/<br>partnerAdapter.replyToReview → POST /api/v1/partner/reviews/{x}/reply/ |
| `components/PartnerRoomCalendar.tsx` | 9 | 0 | partnerAdapter.bulkSetPrice → POST /api/v1/partner/inventory/bulk-price/<br>partnerAdapter.bulkSetRoomInventory → POST /api/v1/partner/room-inventory/bulk/<br>partnerAdapter.createBlock → POST /api/v1/partner/blocks/<br>partnerAdapter.createRoomInventory → POST /api/v1/partner/room-inventory/<br>partnerAdapter.deleteBlock → DELETE /api/v1/partner/blocks/{x}/<br>partnerAdapter.getBlocks<br>partnerAdapter.getDateInventory<br>partnerAdapter.getRatePlans → GET /api/v1/partner/rates/<br>partnerAdapter.getRoomInventory<br>partnerAdapter.updateRoomInventory → PATCH /api/v1/partner/room-inventory/{x}/ |
| `components/PartnerRoomPhotos.tsx` | 0 | 0 | partnerAdapter.deleteRoomPhoto → DELETE /api/v1/partner/rooms/{x}/photos/{x}/<br>partnerAdapter.getRoomPhotos → GET /api/v1/partner/rooms/{x}/photos/<br>partnerAdapter.updateRoomPhoto → PATCH /api/v1/partner/rooms/{x}/photos/{x}/<br>partnerAdapter.uploadRoomPhoto → GET /api/v1/partner/rooms/{x}/photos/ |
| `components/PartnerRoomsManagement.tsx` | 8 | 0 | partnerAdapter.createRoomType → POST /api/v1/partner/rooms/<br>partnerAdapter.deleteRoomType → DELETE /api/v1/partner/rooms/{x}/<br>partnerAdapter.getRoomTypes → GET /api/v1/partner/rooms/<br>partnerAdapter.updateRoomType → PATCH /api/v1/partner/rooms/{x}/<br>partnerAdapter.uploadRoomPhoto → GET /api/v1/partner/rooms/{x}/photos/ |
| `components/PartnerRoomsStatus.tsx` | 1 | 0 | statusAdapter.getPartnerRooms |
| `components/PartnerStatusOverview.tsx` | 1 | 0 | — |
| `components/PartnerStatusTab.tsx` | 1 | 0 | statusAdapter.exportPartnerReconciliation<br>statusAdapter.getPartnerStatus |
| `components/PasswordField.tsx` | 1 | 0 | — |
| `components/PhotoLightbox.tsx` | 3 | 0 | — |
| `components/PromoCarousel.tsx` | 4 | 1 | promotionAdapter.trackClick → GET /api/v1/promotions/{x}/click/ |
| `components/PromotionDialogs.tsx` | 5 | 0 | promotionAdapter.cancelPromotion → GET {x}/promotions/{x}/cancel/<br>promotionAdapter.createPromotion → GET {x}/promotions/<br>promotionAdapter.getPromotionStats → GET {x}/promotions/{x}/stats/ |
| `components/PromotionHotelFinder.tsx` | 1 | 0 | promotionAdapter.searchHotels → GET {x}/promotion-hotels/ |
| `components/PromotionPhotosDialog.tsx` | 2 | 0 | promotionAdapter.deletePromotionPhoto → DELETE {x}/promotions/{x}/photos/{x}/<br>promotionAdapter.getPromotionPhotos → GET {x}/promotions/{x}/photos/<br>promotionAdapter.uploadPromotionPhoto |
| `components/PromotionRegionPanel.tsx` | 3 | 0 | promotionAdapter.getRegionPanel → GET {x}/promotions/regions/ |
| `components/PropertiesMap.tsx` | 2 | 0 | — |
| `components/PropertyCard.tsx` | 1 | 0 | — |
| `components/PropertyGallery.tsx` | 5 | 0 | — |
| `components/PropertyLocationField.tsx` | 1 | 0 | statusAdapter.setPropertyLocation → PATCH /api/v1/admin-panel/properties/{x}/region/ |
| `components/PropertyLocationMap.tsx` | 0 | 1 | — |
| `components/ReviewForm.tsx` | 3 | 0 | accountAdapter.createReview → POST /api/v1/me/reviews/ |
| `components/ReviewsSection.tsx` | 2 | 0 | accountAdapter.getEligibleProperties → GET /api/v1/me/reviews/eligible_properties/<br>accountAdapter.getPropertyScores → GET /api/v1/me/reviews/property_scores/<br>accountAdapter.getPublicReviews → GET /api/v1/me/reviews/public/<br>accountAdapter.getReviews → GET /api/v1/me/reviews/ |
| `components/RoomPhotoQueue.tsx` | 1 | 0 | — |
| `components/RoomSelection.tsx` | 2 | 0 | propertyAdapter.getAvailability → GET /api/v1/properties/{x}/availability/<br>propertyAdapter.getQuote → GET /api/v1/properties/{x}/quote/ |
| `components/SearchFilters.tsx` | 2 | 0 | — |
| `components/SearchForm.tsx` | 2 | 0 | — |
| `components/SegmentedControl.tsx` | 1 | 0 | — |
| `components/ShowOnMapCard.tsx` | 1 | 0 | — |
| `components/StatusCsvButton.tsx` | 2 | 0 | — |
| `components/StatusHotelDetail.tsx` | 0 | 0 | statusAdapter.getHotelDetail → GET {x}/hotels/{x}/{x}/ |
| `components/StatusPagination.tsx` | 2 | 0 | — |
| `components/StatusPeriodSelector.tsx` | 1 | 0 | — |
| `components/StatusRankedTable.tsx` | 1 | 0 | — |
| `components/StatusUserDetail.tsx` | 0 | 0 | statusAdapter.exportUserHistory<br>statusAdapter.getUserDetail |
| `components/ThemeToggle.tsx` | 1 | 0 | — |
| `components/TopBookersLeaderboard.tsx` | 0 | 0 | adminAdapter.getTopBookers |
| `components/TwoFactorCodeForm.tsx` | 3 | 0 | — |
| `pages/AccessDeniedPage.tsx` | 0 | 2 | — |
| `pages/AdminDashboardPage.tsx` | 15 | 0 | — |
| `pages/BookingPage.tsx` | 7 | 0 | bookingAdapter.createBooking → POST /api/v1/bookings/<br>bookingAdapter.getBookings<br>propertyAdapter.getPropertyById → GET /api/v1/properties/{x}/<br>propertyAdapter.getQuote → GET /api/v1/properties/{x}/quote/ |
| `pages/BookingsPage.tsx` | 8 | 2 | accountAdapter.getBookings → GET /api/v1/bookings/ |
| `pages/DestinationsPage.tsx` | 0 | 1 | geographyAdapter.getCities → GET /api/v1/geography/regions/{x}/cities/<br>geographyAdapter.getCountries → GET /api/v1/geography/countries/<br>geographyAdapter.getRegions → GET /api/v1/geography/countries/{x}/regions/ |
| `pages/FavoritesPage.tsx` | 2 | 1 | accountAdapter.getFavorites → GET /api/v1/me/favorites/<br>accountAdapter.removeFavorite → DELETE /api/v1/me/favorites/{x}/ |
| `pages/ForgotPasswordPage.tsx` | 1 | 1 | authAdapter.requestPasswordReset → GET /api/v1/auth/password-reset/request/ |
| `pages/HomePage.tsx` | 1 | 0 | promotionAdapter.getHomePromotions → GET /api/v1/promotions/home/ |
| `pages/InfoPage.tsx` | 0 | 2 | — |
| `pages/LoginPage.tsx` | 1 | 2 | — |
| `pages/NotFoundPage.tsx` | 0 | 1 | — |
| `pages/NotificationsPage.tsx` | 4 | 0 | notificationAdapter.list<br>notificationAdapter.markAllRead<br>notificationAdapter.markRead |
| `pages/PartnerDashboardPage.tsx` | 15 | 0 | partnerAdapter.getProperties → GET /api/v1/partner/properties/ |
| `pages/ProfilePage.tsx` | 3 | 3 | — |
| `pages/PropertyDetailPage.tsx` | 2 | 0 | propertyAdapter.getPropertyById → GET /api/v1/properties/{x}/ |
| `pages/RegisterPage.tsx` | 1 | 1 | — |
| `pages/ResetPasswordPage.tsx` | 1 | 2 | authAdapter.confirmPasswordReset → GET /api/v1/auth/password-reset/confirm/ |
| `pages/SearchResultsPage.tsx` | 3 | 0 | propertyAdapter.getFilterOptions → GET /api/v1/properties/filter-options/<br>propertyAdapter.searchProperties |
| `pages/SupportChatPage.tsx` | 0 | 1 | chatAdapter.mine → GET {x}/messages/ |
| `pages/SupportLookupPage.tsx` | 1 | 2 | adminAdapter.lookupBookingByReferenceCode → GET /api/v1/admin-panel/bookings/lookup/ |
| `pages/TwoFactorSetupPage.tsx` | 6 | 0 | authAdapter.confirmTwoFactorSetup → GET /api/v1/auth/2fa/confirm/<br>authAdapter.startTwoFactorSetup → GET /api/v1/auth/2fa/setup/ |

## Unnecessary things found (not removed: the owner decides)

- `frontend/src/components/Container.tsx`: no screen uses it.
- 17 translation keys in `en.ts` that no screen uses (and their uz/ru twins): `admin.amount`, `admin.provider`,
  `booking.backToDetails`, `booking.backToDetailsLabel`, `booking.nightsOnly`, `booking.ratePlan`, `cancel.close`,
  `no_show_refund_statement`, `no_show_refund_statement_percent`, `partner.stateRegion`, `partner.urlFriendlyIdentifierE`,
  `pay.statusName.partially_refunded`, `pay.statusName.processing`, `promoAdmin.regionFilter`,
  `promoRenewals.col.actions`, `promoRenewals.col.hotel`, `promoRenewals.col.status`.
- Backend `payments/` is only a leftover Django app: the online payment code is already gone (guarded by `core/tests/test_no_online_payments.py`). Its tables hold the booking status history, so they are kept.
