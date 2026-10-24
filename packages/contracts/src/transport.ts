import { Ajv2020, type ValidateFunction } from 'ajv/dist/2020.js';
import { fullFormats } from 'ajv-formats/dist/formats.js';
import { transportSchema } from './generated/schema.js';

const ajv = new Ajv2020({ allErrors: true, strict: false, formats: fullFormats });
const schemaId = 'https://casepilot.local/contracts/transport';
ajv.addSchema(transportSchema, schemaId);

export class ContractError extends Error {
  constructor(model: string, details: string) {
    super(`服务响应不符合 ${model} 契约：${details}`);
    this.name = 'ContractError';
  }
}

/** Compatibility with the frontend's parse boundary, without redefining DTOs. */
export class TransportValidator<T> {
  constructor(private readonly model: string, private readonly validate: ValidateFunction<T>) {}

  parse(value: unknown): T {
    if (!this.validate(value)) throw new ContractError(this.model, ajv.errorsText(this.validate.errors));
    return value;
  }

  array(): TransportValidator<T[]> {
    return new TransportValidator(`${this.model}[]`, ajv.compile<T[]>({
      type: 'array', items: { $ref: `${schemaId}#/$defs/${this.model}` },
    }));
  }
}

export function transportValidator<T>(model: string): TransportValidator<T> {
  return new TransportValidator(model, ajv.compile<T>({ $ref: `${schemaId}#/$defs/${model}` }));
}
