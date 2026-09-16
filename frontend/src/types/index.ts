// API Response Types (placeholders - to be defined when backend APIs are available)
export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

export interface ApiError {
  status: number;
  message: string;
  errors?: Record<string, string[]>;
}

// Common Types
export interface Property {
  id: string;
  name: string;
  description: string;
  location: string;
  pricePerNight: number;
  images: string[];
  amenities: string[];
  capacity: number;
  bedrooms: number;
  bathrooms: number;
}

export interface Booking {
  id: string;
  propertyId: string;
  checkIn: string;
  checkOut: string;
  guests: number;
  totalPrice: number;
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed';
}

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
}
