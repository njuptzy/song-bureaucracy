export class Point extends Array {
    constructor(x, y) {
        super(x, y);
    }

    get x() {
        return this[0];
    }
    get y() {
        return this[1];
    }
    set x(val) {
        this[0] = val;
    }
    set y(val) {
        this[1] = val;
    }

    add(o) {
        return new Point(this.x + o.x, this.y + o.y);
    }
    sub(o) {
        return new Point(this.x - o.x, this.y - o.y);
    }
    mul(o) {
        return new Point(this.x * o, this.y * o);
    }
    len() {
        return Math.sqrt(this.x * this.x + this.y * this.y);
    }
    angle() {
        return Math.atan2(this.y, this.x);
    }
    rotate(ang) {
        return new Point(this.x * Math.cos(ang) - this.y * Math.sin(ang), this.x * Math.sin(ang) + this.y * Math.cos(ang));
    }
    projection(prj) {
        return new Point(...prj(this));
    }
}
