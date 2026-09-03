// Discriminated union of every event in the catalogue
// (IMPLEMENTATION_REACT.md section 4.5). Adding a field is safe; removing
// or renaming one is a breaking change requiring a client release.
//
// Payloads do not carry parish_id: the socket connection is already scoped
// to one parish (ws/parish/<id>/), so the subscribing hook supplies it.

export interface HelloEvent {
  type: "hello";
  server_time: string;
}

export interface DeclarationCreatedEvent {
  type: "declaration.created";
  at: string;
  lot_id: number;
  declaration_id: number;
  bags: number;
  grade: string;
  lot_bags: number;
  lot_min_bags: number;
}

export interface DeclarationGradedEvent {
  type: "declaration.graded";
  at: string;
  declaration_id: number;
  grade: string;
  moisture_pct: string;
  pct_grade1: number;
}

export interface LotClosedEvent {
  type: "lot.closed";
  at: string;
  lot_id: number;
  bags: number;
  bid_count: number;
}

export type ServerEvent = HelloEvent | DeclarationCreatedEvent | DeclarationGradedEvent | LotClosedEvent;
