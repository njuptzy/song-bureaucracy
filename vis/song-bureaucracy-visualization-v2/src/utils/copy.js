export function jsonCopy(o) {
    return o ? JSON.parse(JSON.stringify(o)) : o;
}