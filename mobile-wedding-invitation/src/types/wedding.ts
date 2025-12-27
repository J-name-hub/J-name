export interface AccountInfo {
  bank: string;
  number: string;
  holder: string;
}

export interface WeddingAccountConfig {
  groom: AccountInfo;
  bride: AccountInfo;
  groomFather: AccountInfo;
  groomMother: AccountInfo;
  brideFather: AccountInfo;
  brideMother: AccountInfo;
}

export interface ShuttleContact {
  name: string;
  tel: string;
}

export interface ShuttleInfo {
  location: string;
  departureTime: string;
  contact: ShuttleContact;
}

export interface Venue {
  name: string;
  address: string;
  tel: string;
  naverMapId: string;
  coordinates: {
    latitude: number;
    longitude: number;
  };
  placeId: string;
  mapZoom: string;
  mapNaverCoordinates?: string;
  transportation: {
    subway: string;
    bus: string;
  };
  parking: string;
  groomShuttle?: ShuttleInfo;
  brideShuttle?: ShuttleInfo;
} 